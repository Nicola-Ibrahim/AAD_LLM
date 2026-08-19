import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from infra.storage.sqlite.connection import build_engine
from infra.storage.sqlite.tables import Base


@pytest.fixture(autouse=True)
def isolate_test_data_dir(tmp_path, monkeypatch):
    """Ensure tests write temporary logs and state to an isolated tmp directory."""
    import core.config
    import infra.problems.analyzer
    import synthesis.session
    monkeypatch.setattr(core.config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(infra.problems.analyzer, "DATA_DIR", tmp_path)
    monkeypatch.setattr(synthesis.session, "DATA_DIR", tmp_path)


def pytest_sessionfinish(session, exitstatus):
    """Clean up any dummy test artifacts left in data directory."""
    import shutil
    from core.config import DATA_DIR
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
    db_path = temp_dir / "test.db"
    engine = build_engine(db_path)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session

