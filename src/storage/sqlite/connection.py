from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

def build_engine(db_path: str | Path, echo: bool = False):
    """Creates and configures a SQLite SQLAlchemy engine.
    - Creates parent directories if they don't exist.
    - Registers PRAGMA foreign_keys=ON on every new connection.
    """
    db_path = Path(db_path)
    if db_path.parent:
        db_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(f"sqlite:///{db_path}", echo=echo)

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def build_session_factory(engine) -> sessionmaker[Session]:
    """Creates a thread-safe SQLAlchemy sessionmaker bound to the engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
