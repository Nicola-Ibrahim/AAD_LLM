"""Shared core utilities, configuration, database connection pooling, and schema tables."""

from shared.config import (
    CONFIGS_DIR,
    DATA_DIR,
    NOTEBOOKS_DIR,
    PROJECT_ROOT,
    RESULTS_DIR,
    SCRIPTS_DIR,
    SRC_DIR,
)
from shared.database import (
    build_engine,
    build_session_factory,
    create_db_session_factory,
    ensure_wal_mode,
    get_db_connection,
    get_db_engine,
    initialize_sqlite_storage,
    setup_storage_environment,
)
from shared.execution import (
    AlgorithmExecutor,
    AlgorithmTimeoutException,
    CodeCompiler,
    CodeValidationException,
)
from shared.tables import (
    Base,
    ErrorLogORM,
    ExperimentMode,
    ExperimentORM,
    IterationORM,
)

__all__ = [
    # Directories
    "PROJECT_ROOT",
    "SRC_DIR",
    "DATA_DIR",
    "RESULTS_DIR",
    "NOTEBOOKS_DIR",
    "SCRIPTS_DIR",
    "CONFIGS_DIR",
    # Database primitives
    "get_db_connection",
    "get_db_engine",
    "create_db_session_factory",
    "initialize_sqlite_storage",
    "ensure_wal_mode",
    "build_engine",
    "build_session_factory",
    "setup_storage_environment",
    # Schema Tables
    "Base",
    "ExperimentORM",
    "IterationORM",
    "ErrorLogORM",
    "ExperimentMode",
    # Execution Infrastructure
    "CodeCompiler",
    "AlgorithmExecutor",
    "CodeValidationException",
    "AlgorithmTimeoutException",
]
