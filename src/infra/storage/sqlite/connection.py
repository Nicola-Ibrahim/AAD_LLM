import sqlite3
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session


def ensure_wal_mode(db_path: Path) -> None:
    """Ensures WAL journal mode is set on the DB file before engines are built.

    Idempotent and safe to call multiple times.
    """
    if db_path.parent:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.close()


def build_engine(db_path: Path, echo: bool = False):
    """Creates and configures a SQLite SQLAlchemy engine.
    - Creates parent directories if they don't exist.
    - Ensures WAL journal mode is active on the database file.
    - Configures 60s connection timeout and C-level busy_timeout for multi-process concurrency.
    - Registers PRAGMA foreign_keys=ON on every new connection.
    """
    if db_path.parent:
        db_path.parent.mkdir(parents=True, exist_ok=True)

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


def build_session_factory(engine) -> sessionmaker[Session]:
    """Creates a thread-safe SQLAlchemy sessionmaker bound to the engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
