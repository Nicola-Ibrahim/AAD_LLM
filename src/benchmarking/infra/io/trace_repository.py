"""Trace reader for parsing and scanning empirical IOHprofiler benchmark logs."""

from collections.abc import Callable
import json
from pathlib import Path
import re
from typing import Any

import numpy as np

from shared.config import RESULTS_DIR


class IOHTraceReader:
    """Read-only infrastructure reader managing filesystem access to IOHprofiler `.dat` and `.json` logs."""

    def __init__(self, eval_dir: Path | None = None):
        self.eval_dir = Path(eval_dir) if eval_dir is not None else (RESULTS_DIR / "evaluations" / "traces")

    @staticmethod
    def parse_dat_file(dat_path: Path) -> list[tuple[np.ndarray, np.ndarray]]:
        """Parse an IOHprofiler `.dat` trace file into `(evaluations, raw_objectives)` per run."""
        runs: list[tuple[np.ndarray, np.ndarray]] = []
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
                        runs.append((np.array(current_evals, dtype=float), np.array(current_raw, dtype=float)))
                        current_evals, current_raw = [], []
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        current_evals.append(float(parts[0]))
                        current_raw.append(float(parts[1]))
                    except ValueError:
                        continue

        if current_evals:
            runs.append((np.array(current_evals, dtype=float), np.array(current_raw, dtype=float)))

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
    ) -> dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]]:
        """Scans evaluations directory and loads all .dat runs organized by condition key."""
        data_store: dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]] = {}

        if not self.eval_dir.exists():
            return data_store

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
            if noise_stds and noise_std not in noise_stds:
                continue
            if solvers and solver_name not in solvers:
                continue

            for sc in meta.get("scenarios", []):
                if dim is None:
                    dim = sc.get("dimension")
                if p_id is None or dim is None:
                    continue

                key = (dim, noise_std, p_id)
                if key not in data_store:
                    data_store[key] = {}
                if solver_name not in data_store[key]:
                    data_store[key][solver_name] = []

                dat_p = sc.get("path")
                if dat_p and (json_path.parent / dat_p).exists():
                    data_store[key][solver_name].extend(
                        self.parse_dat_file(json_path.parent / dat_p)
                    )

        return data_store
