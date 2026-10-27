import logging
import shutil
import tempfile
from pathlib import Path

import pytest

from shared.infra.database import Database
from shared.infra.database.tables import Base


@pytest.fixture
def make_progress_logger():
    """Tests configure sinks explicitly, like a notebook or CLI host."""
    handlers = []

    def create(cls, stream, **kwargs):
        name = f"{cls.__module__.split('.')[0]}.test.progress.{len(handlers)}"
        logger = logging.getLogger(name)
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter("%(message)s"))
        old_level = logger.level
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        handlers.append((logger, handler, old_level))
        return cls(logger_name=name, **kwargs)

    yield create
    for logger, handler, level in handlers:
        logger.removeHandler(handler)
        logger.setLevel(level)
        handler.close()


@pytest.fixture(autouse=True)
def isolate_test_data_dir(tmp_path, monkeypatch):
    """Ensure tests write temporary logs and state to an isolated tmp directory."""
    import evolution.infra.engines.llamea.runner
    import evolution.infra.problems.analyzer
    import shared.config
    import shared.infra.logging.runtime

    monkeypatch.setattr(shared.config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(shared.infra.logging.runtime, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(evolution.infra.problems.analyzer, "DATA_DIR", tmp_path)
    monkeypatch.setattr(evolution.infra.engines.llamea.runner, "DATA_DIR", tmp_path)


@pytest.fixture(autouse=True)
def default_test_llm_env(monkeypatch):
    """Ensure test suite does not attempt network connections to live LLM server."""
    monkeypatch.setenv("SKIP_LLM_VALIDATION", "True")
    monkeypatch.setenv("LLM_PROVIDER", "local")
    monkeypatch.setenv("LOCAL_LLM_MODEL", "mock-test-model")


def pytest_sessionfinish(session, exitstatus):
    """Clean up any dummy test artifacts left in data directory."""
    import shutil

    from shared.config import DATA_DIR

    for d in DATA_DIR.glob("**/llamea_dummy*"):
        if d.is_dir():
            shutil.rmtree(d, ignore_errors=True)
    std_05 = DATA_DIR / "ioh_logs" / "2D" / "std_0.5"
    if std_05.exists():
        shutil.rmtree(std_05, ignore_errors=True)


@pytest.fixture
def temp_dir():
    d = Path(tempfile.mkdtemp())
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def db_session_factory(temp_dir):
    """File-backed SQLite database session factory for isolated testing."""
    db_path = temp_dir / "test.db"
    database = Database(f"sqlite:///{db_path}")
    Base.metadata.create_all(database.engine)
    return database.session_factory


@pytest.fixture
def test_db_session_factory():
    """In-memory SQLite database session factory for fast isolated testing."""
    database = Database("sqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    return database.session_factory
