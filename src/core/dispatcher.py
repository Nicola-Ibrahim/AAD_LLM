from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from core.llamea.session import LLaMEASession, SessionResult


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


def dispatch(
    jobs: list[EvolutionJob],
    checkpoint_dir: Path = Path("data/checkpoints"),
    max_workers: int | None = None,
) -> dict[str, SessionResult]:
    """Runs evolution jobs concurrently in a thread pool.

    Args:
        jobs: List of jobs containing a label and a callable returning SessionResult.
        checkpoint_dir: Directory where checkpoints are saved/loaded.
        max_workers: Maximum thread pool workers. Defaults to the number of jobs.

    Returns:
        dict[str, SessionResult]: Dictionary mapping job keys to their evolution results.

    Raises:
        DispatchError: If one or more jobs fail during execution.
    """
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, SessionResult] = {}
    errors: dict[str, Exception] = {}

    if not jobs:
        return results

    workers = max_workers if max_workers is not None else len(jobs)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        def _run_job(job_fn):
            res = job_fn()
            if isinstance(res, LLaMEASession):
                return res.run()
            return res

        future_to_key = {executor.submit(_run_job, job.fn): job.key for job in jobs}

        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                results[key] = future.result()
            except Exception as e:
                errors[key] = e

    if errors:
        raise DispatchError(errors)

    return results
