"""Shared core utilities, configuration, database connection pooling, and schema tables."""

from shared.config import (
    CONFIGS_DIR,
    DATA_DIR,
    DATABASE_URL,
    NOTEBOOKS_DIR,
    PROJECT_ROOT,
    RESULTS_DIR,
    SCRIPTS_DIR,
    SRC_DIR,
)
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
from shared.execution import (
    AlgorithmExecutor,
    AlgorithmTimeoutException,
    CodeCompiler,
    CodeValidationException,
)

__all__ = [
    # Global Config & Directories
    "DATABASE_URL",
    "PROJECT_ROOT",
    "SRC_DIR",
    "DATA_DIR",
    "RESULTS_DIR",
    "NOTEBOOKS_DIR",
    "SCRIPTS_DIR",
    "CONFIGS_DIR",
    # Database primitives
    "create_db_session_factory",
    "initialize_sqlite_storage",
    "ensure_wal_mode",
    "build_engine",
    # Schema Tables
    "Base",
    "ExperimentORM",
    "IterationORM",
    "ErrorLogORM",
    # Execution Infrastructure
    "CodeCompiler",
    "AlgorithmExecutor",
    "CodeValidationException",
    "AlgorithmTimeoutException",
]
