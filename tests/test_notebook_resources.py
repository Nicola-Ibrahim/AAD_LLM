"""Notebook startup owns only module initialization and final shutdown."""

import atexit
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = [
    ("02_synthesis.ipynb", "evolution_module", "EvolutionModule"),
    ("03_benchmark.ipynb", "benchmark_module", "BenchmarkModule"),
    ("04_audit.ipynb", "benchmark_module", "BenchmarkModule"),
    ("analysis/05_reliability_summary.ipynb", "benchmark_module", "BenchmarkModule"),
    ("analysis/06_convergence_ecdf_and_ablations.ipynb", "benchmark_module", "BenchmarkModule"),
    ("analysis/07_noise_robustness.ipynb", "benchmark_module", "BenchmarkModule"),
]


def initialization_source(name: str) -> str:
    notebook = json.loads((ROOT / "notebooks" / name).read_text())
    for cell in notebook["cells"]:
        source = "".join(cell["source"])
        marker = "# Initialize this context once"
        if cell["cell_type"] == "code" and marker in source:
            start = source.index(marker)
            end = source.index("\n", source.index("atexit.register(", start))
            return source[start:end]
    raise AssertionError(f"No module startup found in {name}")


@pytest.mark.parametrize("name,variable,constructor", NOTEBOOKS)
def test_notebook_startup_replaces_old_module_and_registers_one_shutdown_hook(
    name: str, variable: str, constructor: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    registered = []
    monkeypatch.setattr(atexit, "register", registered.append)
    monkeypatch.setattr(atexit, "unregister", registered.remove)
    first, second = MagicMock(), MagicMock()
    namespace = {
        constructor: MagicMock(side_effect=[first, second]),
        "llm": object(),
        "root_dir": ROOT,
        "planned_conditions": (),
    }
    code = compile(initialization_source(name), name, "exec")
    exec(code, namespace)
    assert namespace[variable] is first
    first.close.assert_not_called()
    exec(code, namespace)
    first.close.assert_called_once()
    assert namespace[variable] is second
    assert registered == [second.close]
    registered[0]()
    second.close.assert_called_once()


@pytest.mark.parametrize("name,variable,constructor", NOTEBOOKS)
def test_failed_module_startup_does_not_register_a_shutdown_hook(
    name: str, variable: str, constructor: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    register = MagicMock()
    monkeypatch.setattr(atexit, "register", register)
    namespace = {
        constructor: MagicMock(side_effect=RuntimeError("startup failed")),
        "llm": object(),
        "root_dir": ROOT,
        "planned_conditions": (),
    }
    with pytest.raises(RuntimeError, match="startup failed"):
        exec(compile(initialization_source(name), name, "exec"), namespace)
    assert variable not in namespace
    register.assert_not_called()
