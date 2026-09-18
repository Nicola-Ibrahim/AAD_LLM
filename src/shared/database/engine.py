"""Shared database infrastructure and connection utilities.

Provides thread-safe connection pooling, WAL mode enforcement, and session factories
configured globally via shared.config.DATABASE_URL.
"""

import os
from pathlib import Path
import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from shared.config import DATABASE_URL, PROJECT_ROOT


def ensure_wal_mode(db_path: Path) -> None:
    """Ensures WAL journal mode and normal synchronous are set for SQLite databases.

    Idempotent and safe to call multiple times across concurrent processes.
    """
    if str(db_path) == ":memory:":
        return
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


def build_engine(db_url: str | None = None, *, echo: bool = False) -> Engine:
    """Creates and configures a SQLAlchemy engine using the global DATABASE_URL."""
    if db_url is None:
        env_url = os.getenv("DATABASE_URL")
        if env_url and env_url != "sqlite:///data/db.sqlite3":
            db_url = env_url
        else:
            db_url = DATABASE_URL
    url_obj = make_url(db_url)
    is_sqlite = url_obj.drivername.startswith("sqlite")

    connect_args = {}
    if is_sqlite:
        if url_obj.database and url_obj.database != ":memory:":
            db_path = Path(url_obj.database)
            if not db_path.is_absolute():
                abs_db_path = (PROJECT_ROOT / db_path).resolve()
                db_url = f"sqlite:///{abs_db_path}"
                url_obj = make_url(db_url)
            ensure_wal_mode(Path(url_obj.database))

        connect_args = {
            "check_same_thread": False,
            "timeout": 60.0,
        }

    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=echo,
    )

    if is_sqlite:
        @event.listens_for(engine, "connect")
        def _configure_sqlite(dbapi_conn, _):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=60000")
            cursor.close()

    return engine


def create_db_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    """Creates a thread-safe sessionmaker bound to an engine (or defaults to build_engine())."""
    if engine is None:
        engine = build_engine()
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def initialize_sqlite_storage():
    """Creates an engine using global DATABASE_URL and returns an initialized synthesis repository."""
    from evolution.infra.storage.synthesis import SQLiteSynthesisRepository

    return SQLiteSynthesisRepository(session_factory=create_db_session_factory())


