from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from core.llamea.session import LLaMEASession, SessionResult
from core.checkpoint.manager import CheckpointManager
from infra.storage.manager import ExperimentManager
from infra.storage.checkpoint import CheckpointRepository


@dataclass
class EvolutionJob:
    """A single unit of evolution work to be run in the thread pool."""
    key: str
    fn: Callable[[], SessionResult]


class DispatchError(RuntimeError):
    """Exception raised when one or more evolution jobs fail."""
    def __init__(self, errors: dict[str, Exception]):
        super().__init__(f"Evolution jobs failed: {list(errors.keys())}")
        self.errors = errors


def _bind_context(
    jobs: list[EvolutionJob],
    storage_manager: ExperimentManager,
    checkpoint_repo: CheckpointRepository,
) -> None:
    """Dynamically bind storage_manager and checkpoint_repo into job partial functions if supported."""
    from functools import partial
    import inspect

    for job in jobs:
        fn = job.fn
        if isinstance(fn, partial):
            sig = inspect.signature(fn.func)
            new_keywords = dict(fn.keywords)

            if "storage_manager" in sig.parameters:
                new_keywords["storage_manager"] = storage_manager
            if "checkpoint_repo" in sig.parameters:
                new_keywords["checkpoint_repo"] = checkpoint_repo

            job.fn = partial(fn.func, *fn.args, **new_keywords)


def dispatch(
    jobs: list[EvolutionJob],
    storage_manager: ExperimentManager,
    checkpoint_dir: Path = Path("data/checkpoints"),
    max_workers: int | None = None,
) -> dict[str, SessionResult]:
    """Runs evolution jobs concurrently in a thread pool, persisting results and cleaning up checkpoints.

    Parameters
    ----------
    jobs : list[EvolutionJob]
        List of jobs containing a label and a callable returning SessionResult.
    storage_manager : ExperimentManager
        Persistence coordinator for SQLite records and code blobs.
    checkpoint_dir : Path, optional
        Directory where checkpoints are saved/loaded.
    max_workers : int, optional
        Maximum thread pool workers. Defaults to the number of jobs.

    Returns
    -------
    dict[str, SessionResult]
        Dictionary mapping job keys to their evolution results.

    Raises
    ------
    DispatchError
        If one or more jobs fail during execution or persistence.
    """
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, SessionResult] = {}
    errors: dict[str, Exception] = {}

    if not jobs:
        return results

    # Reusable checkpoint repo constructs once
    repo = CheckpointRepository(checkpoint_dir)

    # Bind required context into jobs if declared
    _bind_context(jobs, storage_manager, repo)

    # Reusable checkpoint manager handles persistence boundaries and deletes
    ckpt_manager = CheckpointManager(repo=repo, storage_manager=storage_manager)

    workers = max_workers if max_workers is not None else len(jobs)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all jobs
        def _run_job(job_fn):
            res = job_fn()
            if isinstance(res, LLaMEASession):
                return res.run()
            return res

        future_to_key = {executor.submit(_run_job, job.fn): job.key for job in jobs}

        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                result = future.result()
                # Run database persistence and checkpoint cleanup
                ckpt_manager.persist_and_cleanup(result)
                results[key] = result
            except Exception as e:
                errors[key] = e

    if errors:
        raise DispatchError(errors)

    return results
