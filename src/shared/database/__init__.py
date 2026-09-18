"""Shared database infrastructure, connection pooling, and schema definitions."""

from shared.config import DATABASE_URL
from shared.database.engine import (
    build_engine,
    create_db_session_factory,
    ensure_wal_mode,
    initialize_sqlite_storage,
)
from shared.database.tables import (
    Base,
    ErrorLogORM,
    ExperimentORM,
    IterationORM,
)

__all__ = [
    # Global Config & Primitives
    "DATABASE_URL",
    "build_engine",
    "create_db_session_factory",
    "ensure_wal_mode",
    "initialize_sqlite_storage",
    # Declarative Schema Tables
    "Base",
    "ErrorLogORM",
    "ExperimentORM",
    "IterationORM",
]



