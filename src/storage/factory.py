from pathlib import Path

from storage.json import JsonStore
from storage.sqlite import SQLiteStore
from storage.manager import ExperimentManager


def get_store(backend: str, path: str | Path) -> ExperimentManager:
    """Factory for selecting a storage backend, wrapped in an ExperimentManager facade.

    Parameters
    ----------
    backend : "json" or "sqlite"
    path    : base directory (json) or db file path (sqlite)
    """
    path_obj = Path(path)
    if backend == "json":
        store = JsonStore(base_dir=path_obj)
        base_dir = path_obj
    elif backend == "sqlite":
        store = SQLiteStore(db_path=path_obj)
        base_dir = path_obj.parent
    else:
        raise ValueError(f"Unknown backend: {backend!r}. Choose 'json' or 'sqlite'.")

    return ExperimentManager(store=store, base_dir=base_dir)
