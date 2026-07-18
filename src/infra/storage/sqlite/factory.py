from pathlib import Path

from infra.storage.sqlite.repository import SQLiteExperimentRepository
from infra.storage.sqlite.connection import build_engine, build_session_factory
from infra.storage.manager import ExperimentManager


def initialize_storage(backend: str, path: str | Path) -> ExperimentManager:
    """Factory for selecting a storage backend, wrapped in an ExperimentManager facade.

    Parameters
    ----------
    backend : "sqlite"
    path    : db file path
    """
    if backend != "sqlite":
        raise ValueError(f"Unknown backend: {backend!r}. Only 'sqlite' is supported.")

    path_obj = Path(path)
    engine = build_engine(path_obj)
    session_factory = build_session_factory(engine)
    store = SQLiteExperimentRepository(session_factory=session_factory)

    # Keep code blobs in the gitignored data/ directory
    base_dir = path_obj.resolve().parent

    return ExperimentManager(store=store, base_dir=base_dir)
