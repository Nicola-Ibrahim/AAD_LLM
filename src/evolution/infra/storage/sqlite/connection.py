"""SQLite connection primitives (re-exported from shared.database for backward compatibility)."""

from shared.database import (
    build_engine,
    build_session_factory,
    ensure_db_dir,
    ensure_wal_mode,
)

__all__ = [
    "ensure_db_dir",
    "ensure_wal_mode",
    "build_engine",
    "build_session_factory",
]
