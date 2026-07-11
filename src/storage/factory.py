from pathlib import Path

from storage.base import ExperimentStore
from storage.json_store import JsonStore
from storage.sqlite_store import SQLiteStore


def get_store(backend: str, path: str | Path) -> ExperimentStore:
    """Factory for selecting a storage backend.

    Parameters
    ----------
    backend : "json" or "sqlite"
    path    : base directory (json) or db file path (sqlite)
    """
    if backend == "json":
        return JsonStore(base_dir=path)
    elif backend == "sqlite":
        return SQLiteStore(db_path=path)
    raise ValueError(f"Unknown backend: {backend!r}. Choose 'json' or 'sqlite'.")
