from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable

from core.llamea.session import LLaMEASession, SessionResult


@dataclass
class EvolutionTask:
    """A single unit of evolution work to be executed in the thread pool."""

    key: str
    fn: Callable[[], SessionResult | LLaMEASession]


class OrchestrationError(RuntimeError):
    """Exception raised when one or more evolution tasks fail."""

    def __init__(self, errors: dict[str, Exception]):
        formatted_details = "\n".join(
            f"  - Task '{key}': {type(err).__name__}: {err}" for key, err in errors.items()
        )
        super().__init__(f"Evolution tasks failed:\n{formatted_details}")
        self.errors = errors


def run_experiments(
    tasks: list[EvolutionTask],
    max_workers: int | None = None,
) -> dict[str, SessionResult]:
    """Runs evolution tasks concurrently in a thread pool.

    Args:
        tasks: List of tasks containing a label and a callable returning SessionResult or LLaMEASession.
        max_workers: Maximum thread pool workers. Defaults to the number of tasks.

    Returns:
        dict[str, SessionResult]: Dictionary mapping task keys to their evolution results.

    Raises:
        OrchestrationError: If one or more tasks fail during execution.
    """
    results: dict[str, SessionResult] = {}
    errors: dict[str, Exception] = {}

    if not tasks:
        return results

    workers = max_workers if max_workers is not None else len(tasks)

    with ThreadPoolExecutor(max_workers=workers) as executor:

        def _run_task(task_fn):
            res = task_fn()
            if isinstance(res, LLaMEASession):
                return res.run()
            return res

        future_to_key = {executor.submit(_run_task, task.fn): task.key for task in tasks}

        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                results[key] = future.result()
            except Exception as e:
                errors[key] = e

    if errors:
        raise OrchestrationError(errors)

    return results
