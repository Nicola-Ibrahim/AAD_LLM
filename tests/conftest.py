import shutil
import tempfile
from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from evolution.infra.storage.sqlite.connection import build_engine
from evolution.infra.storage.sqlite.tables import Base


@pytest.fixture(autouse=True)
def isolate_test_data_dir(tmp_path, monkeypatch):
    """Ensure tests write temporary logs and state to an isolated tmp directory."""
    import evolution.infra.problems.analyzer
    import evolution.synthesis.session
    import shared.config

    monkeypatch.setattr(shared.config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(evolution.infra.problems.analyzer, "DATA_DIR", tmp_path)
    monkeypatch.setattr(evolution.synthesis.session, "DATA_DIR", tmp_path)


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
    engine = build_engine(db_path)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


@pytest.fixture
def test_db_session_factory():
    """In-memory SQLite database session factory for fast isolated testing."""
    engine = build_engine(Path(":memory:"))
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
