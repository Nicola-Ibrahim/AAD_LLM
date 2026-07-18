from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from core.runner import ProblemEvolutionResult
from storage.manager import ExperimentManager


@dataclass
class ExperimentTask:
    """A single unit of experiment work to be run in the thread pool."""
    key: str
    fn: Callable[[], ProblemEvolutionResult]


class ExperimentError(RuntimeError):
    """Exception raised when one or more experiment tasks fail."""
    def __init__(self, errors: dict[str, Exception]):
        super().__init__(f"Experiment tasks failed: {list(errors.keys())}")
        self.errors = errors


def _persist_and_cleanup(
    key: str,
    result: ProblemEvolutionResult,
    storage_manager: ExperimentManager,
    checkpoint_dir: Path,
) -> None:
    """Saves result history and problem profile to database via facade, then deletes checkpoint."""
    # Save to DB via repository facade
    storage_manager.save_experiment(
        history=result.run_history,
        problem=result.problem_profile,
        mode=result.mode,
        llm_name=result.llm_name,
        run_id=result.run_id,
    )

    # Atomic delete of checkpoint file now that it is safely stored in DB
    ckpt_path = checkpoint_dir / f"run{result.run_id}_p{result.problem_id}_d{result.dim}_{result.mode}.ckpt.json"
    if ckpt_path.exists():
        ckpt_path.unlink()

    # Delete the pickle checkpoint directory if it exists
    archive_dir = checkpoint_dir / f"bbob_{result.problem_id}_dim{result.dim}_{result.mode}"
    if archive_dir.exists() and archive_dir.is_dir():
        import shutil
        shutil.rmtree(archive_dir)


def run_experiment(
    tasks: list[ExperimentTask],
    storage_manager: ExperimentManager,
    checkpoint_dir: Path = Path("data/checkpoints"),
    max_workers: int | None = None,
) -> dict[str, ProblemEvolutionResult]:
    """Runs experiment tasks concurrently in a thread pool, persisting results and cleaning up checkpoints.

    Parameters
    ----------
    tasks : list[ExperimentTask]
        List of tasks containing a label and a callable returning ProblemEvolutionResult.
    storage_manager : ExperimentManager
        Persistence coordinator for SQLite records and code blobs.
    checkpoint_dir : Path, optional
        Directory where checkpoints are saved/loaded.
    max_workers : int, optional
        Maximum thread pool workers. Defaults to the number of tasks.

    Returns
    -------
    dict[str, ProblemEvolutionResult]
        Dictionary mapping task keys to their evolution results.

    Raises
    ------
    ExperimentError
        If one or more tasks fail during execution or persistence.
    """
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, ProblemEvolutionResult] = {}
    errors: dict[str, Exception] = {}

    if not tasks:
        return results

    from functools import partial
    import inspect

    # Dynamically inject storage_manager and checkpoint_dir into task partial functions if supported
    for task in tasks:
        fn = task.fn
        if isinstance(fn, partial):
            sig = inspect.signature(fn.func)
            new_keywords = dict(fn.keywords)
            
            if "storage_manager" in sig.parameters:
                new_keywords["storage_manager"] = storage_manager
            if "checkpoint_dir" in sig.parameters:
                new_keywords["checkpoint_dir"] = checkpoint_dir
                
            task.fn = partial(fn.func, *fn.args, **new_keywords)

    workers = max_workers if max_workers is not None else len(tasks)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        future_to_key = {executor.submit(task.fn): task.key for task in tasks}

        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                result = future.result()
                # Run database persistence and checkpoint cleanup
                _persist_and_cleanup(key, result, storage_manager, checkpoint_dir)
                results[key] = result
            except Exception as e:
                errors[key] = e

    if errors:
        raise ExperimentError(errors)

    return results
