"""Application-scoped SQLAlchemy engine and session factory."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from shared.config import DATABASE_URL, PROJECT_ROOT


class Database:
    """Own the configured engine and provide short-lived sessions to repositories.

    Construct one instance at the composition root and pass ``session_factory``
    to SQLAlchemy repositories. Repositories create and close a session per
    operation; application use cases should depend on repositories, not sessions.
    """

    def __init__(self, database_url: str = DATABASE_URL, *, echo: bool = False) -> None:
        url = make_url(database_url)
        is_sqlite = url.drivername.startswith("sqlite")
        connect_args: dict[str, object] = {}

        if is_sqlite:
            if url.database and url.database != ":memory:":
                db_path = Path(url.database)
                if not db_path.is_absolute():
                    db_path = PROJECT_ROOT / db_path
                    url = url.set(database=str(db_path.resolve()))
                self._enable_wal(db_path)
            connect_args = {"check_same_thread": False, "timeout": 60.0}

        self.engine: Engine = create_engine(
            url,
            connect_args=connect_args,
            echo=echo,
        )
        if is_sqlite:
            event.listen(self.engine, "connect", self._configure_sqlite_connection)

        self.session_factory: sessionmaker[Session] = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
        )

    @staticmethod
    def _enable_wal(db_path: Path) -> None:
        """Create the SQLite parent directory and enable persistent WAL mode."""
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(db_path), timeout=60.0) as connection:
            mode = connection.execute("PRAGMA journal_mode").fetchone()
            if mode is None or str(mode[0]).lower() != "wal":
                connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")

    @staticmethod
    def _configure_sqlite_connection(
        dbapi_connection: sqlite3.Connection,
        _connection_record: object,
    ) -> None:
        """Apply per-connection SQLite settings, including synchronous mode."""
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=60000")
            cursor.execute("PRAGMA synchronous=NORMAL")
        finally:
            cursor.close()

    def dispose(self) -> None:
        """Close pooled connections when an application or worker shuts down."""
        self.engine.dispose()
