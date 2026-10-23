"""Composition roots release engines on success, failure and interrupted work."""

import importlib
from unittest.mock import MagicMock

import pytest


@pytest.mark.parametrize("context", ["synthesis", "benchmark"])
@pytest.mark.parametrize("fail_during_work", [False, True])
def test_composition_disposes_database(
    monkeypatch: pytest.MonkeyPatch, context: str, fail_during_work: bool
) -> None:
    module = importlib.import_module(f"bootstrap.{context}")
    database = MagicMock()
    monkeypatch.setattr(module, "Database", lambda: database)
    if context == "synthesis":
        monkeypatch.setattr(module, "SQLiteSynthesisRepository", MagicMock())
        manager = module.build_synthesis_campaign(MagicMock())
    else:
        monkeypatch.setattr(module, "SQLiteSynthesisReadRepository", MagicMock())
        monkeypatch.setattr(module, "ChampionsReadRepository", MagicMock())
        manager = module.build_benchmark_workflow()
    if fail_during_work:
        with pytest.raises(RuntimeError, match="interrupted"):
            with manager:
                database.dispose.assert_not_called()
                raise RuntimeError("interrupted")
    else:
        with manager:
            database.dispose.assert_not_called()
    database.dispose.assert_called_once_with()


@pytest.mark.parametrize("context", ["synthesis", "benchmark"])
def test_failed_construction_also_disposes_database(
    monkeypatch: pytest.MonkeyPatch, context: str
) -> None:
    module = importlib.import_module(f"bootstrap.{context}")
    database = MagicMock()
    monkeypatch.setattr(module, "Database", lambda: database)
    repository = (
        "SQLiteSynthesisRepository" if context == "synthesis" else "SQLiteSynthesisReadRepository"
    )
    monkeypatch.setattr(module, repository, MagicMock(side_effect=RuntimeError("construction")))
    manager = (
        module.build_synthesis_campaign(MagicMock())
        if context == "synthesis"
        else module.build_benchmark_workflow()
    )
    with pytest.raises(RuntimeError, match="construction"):
        with manager:
            pytest.fail("Construction should have failed before yielding")
    database.dispose.assert_called_once_with()
