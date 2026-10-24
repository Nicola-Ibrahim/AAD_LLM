"""Exercise the actual notebook-owned initialization, without databases or campaigns."""

import atexit
import json
import os
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = [
    ("02_synthesis.ipynb", "synthesis", "campaign"),
    ("03_benchmark.ipynb", "benchmark", "workflow"),
    ("04_audit.ipynb", "benchmark", "workflow"),
    ("analysis/05_reliability_summary.ipynb", "analysis", "analysis"),
    ("analysis/06_convergence_ecdf_and_ablations.ipynb", "analysis", "analysis"),
    ("analysis/07_noise_robustness.ipynb", "analysis", "analysis"),
]


def initialization_source(name: str) -> str:
    notebook = json.loads((ROOT / "notebooks" / name).read_text())
    for cell in notebook["cells"]:
        source = "".join(cell["source"])
        marker = "# Notebook resource lifetime"
        if cell["cell_type"] == "code" and marker in source:
            start = source.index(marker)
            end = source.index("\n", source.index("atexit.register(", start))
            return source[start:end]
    raise AssertionError(f"No notebook resource setup found in {name}")


@pytest.mark.parametrize("name,kind,alias", NOTEBOOKS)
def test_notebook_setup_is_rerunnable_and_shutdown_cleanup_is_idempotent(
    name: str, kind: str, alias: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    registered = []
    monkeypatch.setattr(atexit, "register", registered.append)
    monkeypatch.setattr(atexit, "unregister", registered.remove)
    opened, closed = [], []

    @contextmanager
    def scope(*args: object, **kwargs: object):
        service = object()
        opened.append(service)
        try:
            yield service
        finally:
            closed.append(service)

    namespace = {
        f"{kind}_scope": scope,
        "llm": object(),
        "root_dir": ROOT,
        "planned_conditions": (),
        "analysis_config": object(),
    }
    code = compile(initialization_source(name), name, "exec")
    exec(code, namespace)
    assert namespace[alias] is opened[0]
    assert not closed
    exec(code, namespace)
    assert closed == [opened[0]]
    assert namespace[alias] is opened[1]
    assert len(registered) == 1
    registered[0]()
    registered[0]()
    assert closed == opened


@pytest.mark.parametrize("name,kind,alias", NOTEBOOKS)
def test_notebook_initialization_failure_cleans_up_without_registering_a_callback(
    name: str, kind: str, alias: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    register = MagicMock()
    monkeypatch.setattr(atexit, "register", register)
    closed = []

    @contextmanager
    def scope(*args: object, **kwargs: object):
        try:
            raise RuntimeError("initialization failed")
            yield
        finally:
            closed.append(True)

    namespace = {
        f"{kind}_scope": scope,
        "llm": object(),
        "root_dir": ROOT,
        "planned_conditions": (),
        "analysis_config": object(),
    }
    with pytest.raises(RuntimeError, match="initialization failed"):
        exec(compile(initialization_source(name), name, "exec"), namespace)
    assert closed == [True]
    assert alias not in namespace
    register.assert_not_called()


@pytest.mark.parametrize("name,kind,alias", NOTEBOOKS)
def test_notebook_shutdown_callback_does_not_close_parent_resources_in_a_child(
    name: str, kind: str, alias: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    registered, closed = [], []
    monkeypatch.setattr(atexit, "register", registered.append)

    @contextmanager
    def scope(*args: object, **kwargs: object):
        try:
            yield object()
        finally:
            closed.append(True)

    namespace = {
        f"{kind}_scope": scope,
        "llm": object(),
        "root_dir": ROOT,
        "planned_conditions": (),
        "analysis_config": object(),
    }
    exec(compile(initialization_source(name), name, "exec"), namespace)
    owner_pid = os.getpid()
    monkeypatch.setattr(os, "getpid", lambda: owner_pid + 1)
    registered[0]()
    assert not closed
    monkeypatch.setattr(os, "getpid", lambda: owner_pid)
    registered[0]()
    assert closed == [True]
