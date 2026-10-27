"""Solver labels use recorded model IDs; only baseline labels are formatted."""

import re
from collections.abc import Mapping

_BASELINES = {"cmaes": "CMA-ES", "cma_es": "CMA-ES", "cma-es": "CMA-ES", "de": "DE", "pso": "PSO"}
_FOLDER = re.compile(
    r"(.+)_(baseline|thinking|vectorization|guided|champion)(?:_(noisy|implicit))?$"
)


def baseline_name(name: str) -> str:
    return _BASELINES.get(name.lower(), name)


def folder_solver_name(folder: str) -> str:
    """Read our folder format when recorded metadata is unavailable; never infer a model."""
    if match := _FOLDER.fullmatch(folder):
        suffix = {"noisy": " (noise-adapted)", "implicit": " (noise-implicit)"}.get(match[3], "")
        return f"{match[1]} / {match[2]}{suffix}"
    return baseline_name(folder)


def record_solver_name(record: Mapping[str, object]) -> str:
    """Use the actual model ID in provenance, independently of its old directory name."""
    if "baseline" in record:
        return baseline_name(record["baseline"])
    folder = record.get("solver_folder", "")
    suffix = (
        " (noise-implicit)"
        if record.get("mode") == "implicit" or folder.endswith("_implicit")
        else " (noise-adapted)"
        if folder.endswith("_noisy")
        else ""
    )
    return f"{record['model']} / {record.get('strategy', 'baseline')}{suffix}"
