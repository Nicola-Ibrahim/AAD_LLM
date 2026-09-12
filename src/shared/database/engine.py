"""Shared database infrastructure and SQLite connection utilities.

Provides thread-safe connection pooling, WAL mode enforcement, and session factories
shared across bounded contexts without cross-domain dependencies.
"""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session, sessionmaker

from shared.config import DATA_DIR


def ensure_wal_mode(db_path: Path) -> None:
    """Ensures WAL journal mode and normal synchronous are set before engines are built.

    Idempotent and safe to call multiple times across concurrent processes.
    """
    if db_path.parent:
        db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path), timeout=60.0)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode")
        row = cur.fetchone()
        if row is None or str(row[0]).lower() != "wal":
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA synchronous=NORMAL")
    finally:
        conn.close()


def build_engine(db_path: Path = DATA_DIR / "db.sqlite3", echo: bool = False) -> Engine:
    """Creates and configures a SQLite SQLAlchemy engine with WAL mode and concurrency guards."""
    ensure_wal_mode(db_path)

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={
            "check_same_thread": False,
            "timeout": 60.0,
        },
        echo=echo,
    )

    @event.listens_for(engine, "connect")
    def _configure_sqlite(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=60000")
        cursor.close()

    return engine


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Creates a thread-safe SQLAlchemy sessionmaker bound to the engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def create_db_session_factory(
    path: Path = DATA_DIR / "db.sqlite3",
) -> sessionmaker[Session]:
    """Creates an engine and returns a thread-safe session factory for the given SQLite path."""
    engine = build_engine(path)
    return build_session_factory(engine)


@contextmanager
def get_db_connection(
    path: Path = DATA_DIR / "db.sqlite3",
) -> Generator[Connection, None, None]:
    """Context manager yielding a live database connection for query execution."""
    engine = build_engine(path)
    with engine.connect() as conn:
        yield conn


def initialize_sqlite_storage(
    path: Path = DATA_DIR / "db.sqlite3",
):
    """Creates an engine and returns an initialized SQLite synthesis repository."""
    from evolution.infra.storage.synthesis import SQLiteSynthesisRepository

    session_factory = create_db_session_factory(path)
    return SQLiteSynthesisRepository(session_factory=session_factory)
