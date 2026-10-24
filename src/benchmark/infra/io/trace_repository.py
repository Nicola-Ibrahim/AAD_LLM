"""Trace reader for parsing and scanning empirical IOHprofiler benchmark logs."""

import json
import re
import shutil
from collections import defaultdict, deque
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import ioh
import numpy as np

from benchmark.application.interfaces.benchmark_state_store import BenchmarkStateStore
from benchmark.application.interfaces.benchmark_trace_reader import BenchmarkTraceReader
from benchmark.domain.benchmark_results import (
    executed_trial_count,
)
from benchmark.domain.services.condition_status import inspect_condition
from benchmark.domain.trial_schedule import TrialIdentity, matching_trial_indices
from benchmark.domain.vos import BenchmarkCondition, BenchmarkDataset, RunTrace
from shared.config import RESULTS_DIR


class IOHTraceReader(BenchmarkTraceReader):
    """Read-only infrastructure reader managing filesystem access to IOHprofiler `.dat` and `.json` logs."""

    def __init__(self, benchmark_dir: Path = RESULTS_DIR / "ioh_traces") -> None:
        self._benchmark_dir = Path(benchmark_dir)

    @property
    def benchmark_dir(self) -> Path:
        """Directory containing IOH traces."""
        return self._benchmark_dir

    @staticmethod
    def parse_dat_file(dat_path: Path) -> list[RunTrace]:
        """Parse an IOHprofiler `.dat` trace file into `RunTrace` value objects per run."""
        runs: list[RunTrace] = []
        current_evals: list[float] = []
        current_raw: list[float] = []

        if not dat_path.exists():
            return runs

        with open(dat_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(("function", "evaluations", '"evaluations"', "#", "instance")):
                    if current_evals:
                        runs.append(
                            RunTrace(
                                evaluations=np.array(current_evals, dtype=float),
                                raw_objectives=np.array(current_raw, dtype=float),
                            )
                        )
                        current_evals, current_raw = [], []
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        eval_val = float(parts[0])
                        raw_str = parts[1].strip()
                        if raw_str.lower() in ("none", "null", "nan"):
                            if current_raw:
                                raw_val = current_raw[-1]
                            else:
                                continue
                        else:
                            raw_val = float(raw_str)
                        current_evals.append(eval_val)
                        current_raw.append(raw_val)
                    except ValueError:
                        continue

        if current_evals:
            runs.append(
                RunTrace(
                    evaluations=np.array(current_evals, dtype=float),
                    raw_objectives=np.array(current_raw, dtype=float),
                )
            )

        return runs

    def get_run_count(self, solver_dir: Path) -> int:
        """Extract number of completed runs for a solver folder."""
        if not solver_dir.exists():
            return 0

        prov_path = solver_dir / "provenance.json"
        if prov_path.exists():
            try:
                with open(prov_path, "r", encoding="utf-8") as pf:
                    prov = json.load(pf)
                clean_errors = prov.get("clean_errors")
                if clean_errors is not None and isinstance(clean_errors, list):
                    return executed_trial_count(prov)
                n = prov.get("n_runs")
                if n is not None and int(n) > 0:
                    return int(n)
            except Exception:
                pass

        ioh_jsons = [f for f in solver_dir.glob("**/*.json") if "IOHprofiler" in f.name]
        if ioh_jsons:
            try:
                with open(ioh_jsons[0], "r", encoding="utf-8") as jf:
                    meta = json.load(jf)
                runs = meta.get("scenarios", [{}])[0].get("runs", [])
                if runs:
                    return len(runs)
            except Exception:
                pass

        dat_files = [f for f in solver_dir.glob("**/*.dat") if f.stat().st_size > 0]
        return len(dat_files)

    def load_provenance_records(self) -> list[dict[str, object]]:
        """Load current terminal-result records, excluding historical skipped tails."""
        records: list[dict[str, object]] = []
        for path in sorted(self.benchmark_dir.rglob("provenance.json")):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(record, dict):
                continue
            inspection = inspect_condition(
                code_available=True,
                directory_exists=True,
                provenance=record,
                expected_code_hash=None,
                expected_trials=1,
                expected_budget=None,  # Raw reading preserves historical protocols.
            )
            if inspection.reason not in {"complete", "partial", "not_started"}:
                continue
            count = inspection.reusable_trials
            records.append(
                {
                    **record,
                    "clean_errors": record.get("clean_errors", record.get("errors", []))[:count],
                    "n_runs": count,
                    "solver_folder": path.parent.name,
                    "trace_directory": str(path.parent),
                }
            )
        return records

    def load_benchmark_traces(
        self,
        dims: list[int] | None = None,
        problems: list[int] | None = None,
        noise_stds: list[float] | None = None,
        solvers: list[str] | None = None,
        solver_resolver: Callable[[str], str] | None = None,
        trial_schedule: tuple[TrialIdentity, ...] = (),
    ) -> BenchmarkDataset:
        """Scans evaluations directory and loads all .dat runs organized in a strongly-typed BenchmarkDataset."""
        dataset = BenchmarkDataset()

        if not self.benchmark_dir.exists():
            return dataset
        records = self.load_provenance_records()
        by_directory = {Path(r["trace_directory"]).resolve(): r for r in records}

        for json_path in self.benchmark_dir.glob("**/*.json"):
            if "provenance" in json_path.name:
                continue

            try:
                with open(json_path, "r", encoding="utf-8") as jf:
                    raw_metadata = json.load(jf)
            except Exception:
                continue
            if not isinstance(raw_metadata, dict):
                continue
            meta: dict[str, object] = raw_metadata

            path_str = str(json_path.relative_to(self.benchmark_dir))
            dim_m = re.search(r"(\d+)D", path_str)
            dim = int(dim_m.group(1)) if dim_m else None
            noise_m = re.search(r"std_([\d\.]+)", path_str)
            noise_std = float(noise_m.group(1)) if noise_m else 0.0
            raw_problem_id = meta.get("function_id")
            p_id = int(raw_problem_id) if isinstance(raw_problem_id, (int, float)) else None
            if p_id is None:
                p_m = re.search(r"f(\d+)", path_str)
                p_id = int(p_m.group(1)) if p_m else None

            parent_name = json_path.parent.name
            if "dummy" in parent_name.lower():
                continue

            solver_name = solver_resolver(parent_name) if solver_resolver else parent_name

            if dims and dim is not None and dim not in dims:
                continue
            if problems and p_id is not None and p_id not in problems:
                continue
            if noise_stds and not any(np.isclose(noise_std, n) for n in noise_stds):
                continue
            if solvers and solver_name not in solvers:
                continue

            scenarios = meta.get("scenarios", [])
            if not isinstance(scenarios, list):
                continue
            for sc in scenarios:
                if not isinstance(sc, dict):
                    continue
                if dim is None:
                    raw_dim = sc.get("dimension")
                    dim = int(raw_dim) if isinstance(raw_dim, (int, float)) else None
                if p_id is None or dim is None:
                    continue

                cond = BenchmarkCondition(dim=dim, noise_std=noise_std, problem_id=p_id)
                dat_p = sc.get("path")
                if isinstance(dat_p, str) and dat_p and (json_path.parent / dat_p).exists():
                    parsed_runs = self.parse_dat_file(json_path.parent / dat_p)
                    if not trial_schedule:
                        for run in parsed_runs:
                            dataset.add_run(cond, solver_name, run)
                        continue
                    record = by_directory.get(json_path.parent.resolve(), {})
                    selected_indices = set(matching_trial_indices(record, trial_schedule))
                    explicit_indices = {
                        trial["trace_run_index"]: index
                        for index, trial in enumerate(record.get("trial_records", []))
                        if trial.get("trace_run_index") is not None
                    }
                    explicit_records = set(explicit_indices.values())
                    indices_by_instance: dict[int, deque[int]] = defaultdict(deque)
                    for index, (instance, used) in enumerate(
                        zip(record.get("instance_ids", []), record.get("evaluations_used", []))
                    ):
                        if (
                            index < executed_trial_count(record)
                            and used > 0
                            and index not in explicit_records
                        ):
                            indices_by_instance[instance].append(index)
                    logged_runs = [r for r in sc.get("runs", []) if r.get("evals", 0) > 0]
                    # Missing/misaligned trace identities must not be guessed from trial counts.
                    if len(logged_runs) != len(parsed_runs):
                        continue
                    for trace_index, (logged, run) in enumerate(zip(logged_runs, parsed_runs)):
                        candidates = indices_by_instance[logged.get("instance")]
                        index = explicit_indices.get(trace_index)
                        if index is None:
                            if not candidates:
                                continue
                            index = candidates.popleft()
                        if index in selected_indices and record["instance_ids"][
                            index
                        ] == logged.get("instance"):
                            dataset.add_run(cond, solver_name, run)

        # Only confirmed pre-query execution failures get empty trace entries.
        # Missing trace files for otherwise evaluated trials stay missing.
        for record in records:
            dim, noise_std, p_id = (
                int(record["dim"]),
                float(record["noise_std"]),
                int(record["problem_id"]),
            )
            if (dims and dim not in dims) or (problems and p_id not in problems):
                continue
            if noise_stds and not any(np.isclose(noise_std, n) for n in noise_stds):
                continue
            folder = str(record["solver_folder"])
            solver_name = solver_resolver(folder) if solver_resolver else folder
            if solvers and solver_name not in solvers:
                continue
            condition = BenchmarkCondition(dim=dim, noise_std=noise_std, problem_id=p_id)
            selected_indices = set(matching_trial_indices(record, trial_schedule))
            for index, (error, used) in enumerate(
                zip(record["clean_errors"], record.get("evaluations_used", []))
            ):
                if index not in selected_indices:
                    continue
                if float(error) == float("inf") and used == 0:
                    dataset.add_run(
                        condition,
                        solver_name,
                        RunTrace(
                            evaluations=np.array([], dtype=float),
                            raw_objectives=np.array([], dtype=float),
                        ),
                    )
        return dataset


class BenchmarkStateRepository(BenchmarkStateStore):
    """Infrastructure repository managing read/write operations for benchmark evaluation provenance and log merging."""

    def __init__(self, benchmark_dir: Path = RESULTS_DIR / "ioh_traces") -> None:
        self._benchmark_dir = Path(benchmark_dir)

    @property
    def benchmark_dir(self) -> Path:
        """Directory containing evaluation traces and provenance."""
        return self._benchmark_dir

    def condition_directory(self, dim: int, noise_std: float, problem_id: int, solver: str) -> Path:
        return self.benchmark_dir / f"{dim}D" / f"std_{noise_std}" / f"f{problem_id}" / solver

    def transfer_directory(
        self,
        source_problem_id: int,
        dim: int,
        noise_std: float,
        problem_id: int,
        solver: str,
        code_hash: str,
    ) -> Path:
        return (
            self.benchmark_dir.parent
            / "cross_function_traces"
            / f"source_f{source_problem_id}"
            / f"{dim}D"
            / f"std_{noise_std}"
            / f"f{problem_id}"
            / f"{solver}_{code_hash[:12]}"
        )

    def remove_solver_traces(self, solver_dir: Path) -> None:
        """Remove one stale solver condition directory before a clean evaluation."""
        if solver_dir.exists():
            shutil.rmtree(solver_dir)

    @staticmethod
    def solver_directory_exists(solver_dir: Path) -> bool:
        return solver_dir.is_dir()

    def get_trace_run_count(self, solver_dir: Path) -> int:
        count = 0
        for path in solver_dir.glob("IOHprofiler*.json"):
            metadata = json.loads(path.read_text(encoding="utf-8"))
            count += sum(
                int(run.get("evals", 0) > 0)
                for scenario in metadata.get("scenarios", [])
                for run in scenario.get("runs", [])
            )
        return count

    @contextmanager
    def open_run_logger(
        self, target_dir: Path, algorithm_name: str, incremental: bool
    ) -> Iterator[object]:
        """Own temporary log staging, IOH logger construction, and incremental merging."""
        if incremental:
            from tempfile import TemporaryDirectory

            with TemporaryDirectory() as tmpdir:
                run_dir = Path(tmpdir) / target_dir.name
                run_dir.parent.mkdir(parents=True, exist_ok=True)
                logger = ioh.logger.Analyzer(
                    root=str(run_dir.parent),
                    folder_name=run_dir.name,
                    algorithm_name=algorithm_name,
                    store_positions=False,
                )
                try:
                    yield logger
                finally:
                    logger.close()
                    self.merge_run_logs(run_dir, target_dir)
            return

        target_dir.parent.mkdir(parents=True, exist_ok=True)
        logger = ioh.logger.Analyzer(
            root=str(target_dir.parent),
            folder_name=target_dir.name,
            algorithm_name=algorithm_name,
            store_positions=False,
        )
        try:
            yield logger
        finally:
            logger.close()

    def read_provenance(self, solver_dir: Path) -> dict[str, object] | None:
        """Reads and parses provenance.json for a solver directory if it exists."""
        prov_path = solver_dir / "provenance.json"
        if not prov_path.exists():
            return None
        try:
            with open(prov_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def write_provenance(self, solver_dir: Path, data: dict[str, object]) -> None:
        """Persists complete metadata, metrics, and trial arrays into provenance.json."""
        solver_dir.mkdir(parents=True, exist_ok=True)
        prov_path = solver_dir / "provenance.json"
        with open(prov_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_run_count(self, solver_dir: Path) -> int:
        """Determines the number of completed trials recorded in provenance or dat files."""
        prov = self.read_provenance(solver_dir)
        if prov is not None:
            clean_errors = prov.get("clean_errors")
            if clean_errors is not None and isinstance(clean_errors, list):
                return executed_trial_count(prov)
            n_runs = prov.get("n_runs")
            if n_runs is not None and int(n_runs) > 0:
                return int(n_runs)

        ioh_jsons = [f for f in solver_dir.glob("**/*.json") if "IOHprofiler" in f.name]
        if ioh_jsons:
            try:
                with open(ioh_jsons[0], "r", encoding="utf-8") as jf:
                    meta = json.load(jf)
                runs = meta.get("scenarios", [{}])[0].get("runs", [])
                if runs:
                    return len(runs)
            except Exception:
                pass

        dat_files = [f for f in solver_dir.glob("**/*.dat") if f.stat().st_size > 0]
        return len(dat_files)

    @staticmethod
    def merge_run_logs(source_dir: Path, target_dir: Path) -> None:
        """Merge incremental IOHprofiler .dat and .json run traces into primary target directory."""
        for src_dat in source_dir.glob("**/*.dat"):
            rel = src_dat.relative_to(source_dir)
            tgt_dat = target_dir / rel
            tgt_dat.parent.mkdir(parents=True, exist_ok=True)
            if tgt_dat.exists() and tgt_dat.stat().st_size > 0:
                content = src_dat.read_text(encoding="utf-8")
                with open(tgt_dat, "a", encoding="utf-8") as f:
                    f.write("\n" + content)
            else:
                shutil.copy2(src_dat, tgt_dat)

        for src_json in source_dir.glob("**/*.json"):
            if "provenance" in src_json.name:
                continue
            rel = src_json.relative_to(source_dir)
            tgt_json = target_dir / rel
            tgt_json.parent.mkdir(parents=True, exist_ok=True)
            if tgt_json.exists():
                try:
                    src_data = json.loads(src_json.read_text(encoding="utf-8"))
                    tgt_data = json.loads(tgt_json.read_text(encoding="utf-8"))
                    src_runs = src_data.get("scenarios", [{}])[0].get("runs", [])
                    if "scenarios" in tgt_data and tgt_data["scenarios"]:
                        tgt_data["scenarios"][0].setdefault("runs", []).extend(src_runs)
                        tgt_json.write_text(json.dumps(tgt_data, indent=2), encoding="utf-8")
                except Exception:
                    pass
            else:
                shutil.copy2(src_json, tgt_json)
