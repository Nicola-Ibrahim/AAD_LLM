"""Verify infrastructure cleanup and the small notebook setup that uses it."""

import atexit
import json
import os
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import shared.infra.di as composition
from shared.infra.lifecycle import WorkflowScope

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = [
    ("02_synthesis.ipynb", "synthesis", "campaign"),
    ("03_benchmark.ipynb", "benchmark", "benchmark_coordinator"),
    ("04_audit.ipynb", "audit", "coverage_audit"),
    ("analysis/05_reliability_summary.ipynb", "analysis", "reliability_analysis"),
    ("analysis/06_convergence_ecdf_and_ablations.ipynb", "analysis", "profile_analysis"),
    ("analysis/07_noise_robustness.ipynb", "analysis", "noise_analysis"),
]


def initialization_source(name: str) -> str:
    notebook = json.loads((ROOT / "notebooks" / name).read_text())
    for cell in notebook["cells"]:
        source = "".join(cell["source"])
        marker = "# Prepare services once; infrastructure owns shutdown cleanup."
        if cell["cell_type"] == "code" and marker in source:
            start = source.index(marker)
            lines = source[start:].splitlines()
            end = max(i for i, line in enumerate(lines) if "services.get(" in line) + 1
            return "\n".join(lines[:end])
    raise AssertionError(f"No service setup found in {name}")


def setup_namespace() -> dict[str, object]:
    namespace = {
        "WorkflowScope": WorkflowScope,
        "EvolutionProvider": MagicMock(),
        "BenchmarkProvider": MagicMock(),
        "llm": object(),
        "root_dir": ROOT,
        "planned_conditions": (),
        "analysis_config": object(),
    }
    for symbol in (
        "LLMClient",
        "BenchmarkConfig",
        "SynthesisCampaignCoordinator",
        "BenchmarkCoordinator",
        "ChampionSelectionService",
        "SQLiteSynthesisReadRepository",
        "ModelNames",
        "BenchmarkAuditService",
        "AnalyzeReliability",
        "AnalyzeEcdfAndConvergence",
        "AnalyzePerformance",
        "AnalyzeNoiseRobustness",
        "AnalysisResultsStore",
    ):
        namespace[symbol] = object()
    return namespace


@pytest.mark.parametrize("name,kind,alias", NOTEBOOKS)
def test_notebook_setup_is_rerunnable_and_cleanup_is_idempotent(name, kind, alias, monkeypatch):
    registered, opened, closed = [], [], []
    monkeypatch.setattr(atexit, "register", registered.append)
    monkeypatch.setattr(atexit, "unregister", registered.remove)

    @contextmanager
    def scope(*args: object, **kwargs: object):
        service = object()
        opened.append(service)
        try:
            yield MagicMock(get=lambda cls: service)
        finally:
            closed.append(service)

    monkeypatch.setattr(composition, "container_scope", scope)
    namespace = setup_namespace()
    code = compile(initialization_source(name), name, "exec")
    exec(code, namespace)
    assert namespace[alias] is opened[0]
    assert not closed
    exec(code, namespace)
    assert namespace[alias] is opened[1]
    assert closed == [opened[0]]
    assert len(registered) == 1
    cleanup = registered[0]
    cleanup()
    cleanup()
    assert closed == opened
    assert not registered


@pytest.mark.parametrize("name,kind,alias", NOTEBOOKS)
def test_service_construction_failure_closes_scope_and_unregisters_cleanup(
    name, kind, alias, monkeypatch
):
    registered = []
    monkeypatch.setattr(atexit, "register", registered.append)
    monkeypatch.setattr(atexit, "unregister", registered.remove)
    closed = []

    @contextmanager
    def scope(*args: object, **kwargs: object):
        try:
            yield MagicMock(get=MagicMock(side_effect=RuntimeError("construction failed")))
        finally:
            closed.append(True)

    monkeypatch.setattr(composition, "container_scope", scope)
    namespace = setup_namespace()
    with pytest.raises(RuntimeError, match="construction failed"):
        exec(compile(initialization_source(name), name, "exec"), namespace)
    assert closed == [True]
    assert alias not in namespace
    assert not registered


@pytest.mark.parametrize("name,kind,alias", NOTEBOOKS)
def test_notebook_cleanup_does_not_finalize_parent_resources_in_forked_child(
    name, kind, alias, monkeypatch
):
    registered, closed = [], []
    monkeypatch.setattr(atexit, "register", registered.append)

    @contextmanager
    def scope(*args: object, **kwargs: object):
        try:
            yield MagicMock()
        finally:
            closed.append(True)

    monkeypatch.setattr(composition, "container_scope", scope)
    monkeypatch.setattr(atexit, "unregister", registered.remove)
    exec(compile(initialization_source(name), name, "exec"), setup_namespace())
    parent_pid = os.getpid()
    monkeypatch.setattr(os, "getpid", lambda: parent_pid + 1)
    registered[0]()
    assert not closed
    monkeypatch.setattr(os, "getpid", lambda: parent_pid)
    registered[0]()
    assert closed == [True]


def test_closed_scope_cannot_resolve_services(monkeypatch):
    monkeypatch.setattr(composition, "container_scope", lambda *a, **kw: scope_stub())
    scope = WorkflowScope(context={}, request_context={})
    scope.close()
    scope.close()
    with pytest.raises(RuntimeError, match="closed"):
        scope.get(str)


@contextmanager
def scope_stub():
    yield MagicMock()


def test_inherited_scope_cannot_resolve_parent_services(monkeypatch):
    monkeypatch.setattr(composition, "container_scope", lambda *a, **kw: scope_stub())
    scope = WorkflowScope(context={}, request_context={})
    parent_pid = os.getpid()
    monkeypatch.setattr(os, "getpid", lambda: parent_pid + 1)
    try:
        with pytest.raises(RuntimeError, match="process-local"):
            scope.get(str)
    finally:
        monkeypatch.setattr(os, "getpid", lambda: parent_pid)
        scope.close()
