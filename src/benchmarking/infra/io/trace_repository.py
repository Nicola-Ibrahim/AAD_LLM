"""Trace reader for parsing and scanning empirical IOHprofiler benchmark logs."""

from collections.abc import Callable
import json
from pathlib import Path
import re
import shutil
from typing import Any

import numpy as np

from benchmarking.domain.vos import EvaluationCondition, EvaluationDataset, RunTrace
from shared.config import RESULTS_DIR


class IOHTraceReader:
    """Read-only infrastructure reader managing filesystem access to IOHprofiler `.dat` and `.json` logs."""

    def __init__(self, eval_dir: Path = RESULTS_DIR / "ioh_traces"):
        self.eval_dir = Path(eval_dir)

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
                    return len(clean_errors)
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

    def load_evaluation_traces(
        self,
        dims: list[int] | None = None,
        problems: list[int] | None = None,
        noise_stds: list[float] | None = None,
        solvers: list[str] | None = None,
        solver_resolver: Callable[[str], str] | None = None,
    ) -> EvaluationDataset:
        """Scans evaluations directory and loads all .dat runs organized in a strongly-typed EvaluationDataset."""
        dataset = EvaluationDataset()

        if not self.eval_dir.exists():
            return dataset

        for json_path in self.eval_dir.glob("**/*.json"):
            if "provenance" in json_path.name:
                continue

            try:
                with open(json_path, "r", encoding="utf-8") as jf:
                    meta: dict[str, Any] = json.load(jf)
            except Exception:
                continue

            path_str = str(json_path.relative_to(self.eval_dir))
            dim_m = re.search(r"(\d+)D", path_str)
            dim = int(dim_m.group(1)) if dim_m else None
            noise_m = re.search(r"std_([\d\.]+)", path_str)
            noise_std = float(noise_m.group(1)) if noise_m else 0.0
            p_id = meta.get("function_id")
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

            for sc in meta.get("scenarios", []):
                if dim is None:
                    dim = sc.get("dimension")
                if p_id is None or dim is None:
                    continue

                cond = EvaluationCondition(dim=dim, noise_std=noise_std, problem_id=p_id)
                dat_p = sc.get("path")
                if dat_p and (json_path.parent / dat_p).exists():
                    parsed_runs = self.parse_dat_file(json_path.parent / dat_p)
                    for r in parsed_runs:
                        dataset.add_run(cond, solver_name, r)

        return dataset


class EvaluationStateRepository:
    """Infrastructure repository managing read/write operations for benchmark evaluation provenance and log merging."""

    def __init__(self, eval_dir: Path = RESULTS_DIR / "ioh_traces"):
        self.eval_dir = Path(eval_dir)

    def read_provenance(self, solver_dir: Path) -> dict[str, Any] | None:
        """Reads and parses provenance.json for a solver directory if it exists."""
        prov_path = solver_dir / "provenance.json"
        if not prov_path.exists():
            return None
        try:
            with open(prov_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def write_provenance(self, solver_dir: Path, data: dict[str, Any]) -> None:
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
                return len(clean_errors)
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
