import shutil
import tempfile
from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from infra.storage.sqlite.connection import build_engine
from infra.storage.sqlite.tables import Base


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
