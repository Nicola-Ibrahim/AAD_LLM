import shutil
import tempfile
from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from shared.database.engine import build_engine
from shared.database.tables import Base


@pytest.fixture(autouse=True)
def isolate_test_data_dir(tmp_path, monkeypatch):
    """Ensure tests write temporary logs and state to an isolated tmp directory."""
    import evolution.infra.engines.llamea.runner
    import evolution.infra.problems.analyzer
    import shared.config

    monkeypatch.setattr(shared.config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(evolution.infra.problems.analyzer, "DATA_DIR", tmp_path)
    monkeypatch.setattr(evolution.infra.engines.llamea.runner, "DATA_DIR", tmp_path)


@pytest.fixture(autouse=True)
def default_test_llm_env(monkeypatch):
    """Ensure test suite does not attempt network connections to live LLM server."""
    monkeypatch.setenv("SKIP_LLM_VALIDATION", "True")
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
def db_session_factory(temp_dir, monkeypatch):
    """File-backed SQLite database session factory for isolated testing."""
    db_path = temp_dir / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    engine = build_engine()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


@pytest.fixture
def test_db_session_factory(monkeypatch):
    """In-memory SQLite database session factory for fast isolated testing."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    engine = build_engine()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

