"""Generic process pool runner for parallel task execution.

Provides a decoupled, reusable concurrency engine using ProcessPoolExecutor.
Has zero dependencies on application services or domain contracts.
"""

from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed

from evolution.domain.exceptions import OrchestrationError


class ProcessPoolRunner:
    """Manages multi-core parallel execution of arbitrary callable units via ProcessPoolExecutor."""

    def __init__(self, max_workers: int | None = None) -> None:
        """Initializes the runner with worker configuration.

        Args:
            max_workers: Maximum process pool worker processes. If None, defaults to the number of tasks.
        """
        self.max_workers = max_workers

    def run[T, R](
        self,
        fn: Callable[[T], R],
        items: list[T],
        key_fn: Callable[[T], str],
    ) -> dict[str, R]:
        """Executes a function across items concurrently in a process pool.

        Args:
            fn: A picklable top-level function taking an item of type T and returning R.
            items: List of input items.
            key_fn: Callable extracting a unique string identifier from each item.

        Returns:
            dict[str, R]: Dictionary mapping each item's key to its result.

        Raises:
            OrchestrationError: If one or more tasks fail during execution.
        """
        if not items:
            return {}

        results: dict[str, R] = {}
        errors: dict[str, Exception] = {}
        workers = self.max_workers if self.max_workers is not None else len(items)

        with ProcessPoolExecutor(max_workers=workers) as executor:
            future_to_key = {
                executor.submit(fn, item): key_fn(item) for item in items
            }

            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    errors[key] = e

        if errors:
            raise OrchestrationError(errors) from None

        return results
