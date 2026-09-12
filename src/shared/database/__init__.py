"""Shared database infrastructure, connection pooling, and schema definitions."""

from shared.database.engine import (
    build_engine,
    build_session_factory,
    create_db_session_factory,
    ensure_wal_mode,
    get_db_connection,
    initialize_sqlite_storage,
)
from shared.database.tables import (
    Base,
    ErrorLogORM,
    ExperimentORM,
    IterationORM,
)

__all__ = [
    # Engine & Session Primitives
    "build_engine",
    "build_session_factory",
    "create_db_session_factory",
    "ensure_wal_mode",
    "get_db_connection",
    "initialize_sqlite_storage",
    # Declarative Schema Tables
    "Base",
    "ErrorLogORM",
    "ExperimentORM",
    "IterationORM",
]
