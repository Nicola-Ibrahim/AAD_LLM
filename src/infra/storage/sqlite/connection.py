from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session


def build_engine(db_path: Path, echo: bool = False):
    """Creates and configures a SQLite SQLAlchemy engine.
    - Creates parent directories if they don't exist.
    - Registers PRAGMA foreign_keys=ON on every new connection.
    """
    if db_path.parent:
        db_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={
            "check_same_thread": False,
            "timeout": 15,
        },
        echo=echo,
    )

    @event.listens_for(engine, "connect")
    def _configure_sqlite(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

    return engine


def build_session_factory(engine) -> sessionmaker[Session]:
    """Creates a thread-safe SQLAlchemy sessionmaker bound to the engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
