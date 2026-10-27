"""Multiprocessing worker pool for parallel experiment execution.

Implements application task dispatch using ProcessPoolExecutor and host-owned logging.
"""

import logging
from collections.abc import Callable
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from typing import Generic, TypeVar

from evolution.application.exceptions import OrchestrationError, ProviderError
from evolution.application.interfaces.experiment_worker_pool import ExperimentWorkerPool
from shared.application.errors import ArtifactError, StorageError
from shared.infra.logging.runtime import configure_worker_logging, current_runtime

T = TypeVar("T")
R = TypeVar("R")


class ProcessWorkerPool(Generic[T, R], ExperimentWorkerPool[T, R]):
    """Manages multi-core parallel execution of arbitrary callable units via ProcessPoolExecutor."""

    def __init__(self, max_workers: int | None = None) -> None:
        """Initialize the pool with worker configuration.

        Args:
            max_workers: Maximum process pool worker processes. If None, defaults to the number of tasks.
        """
        self.max_workers = max_workers

    def execute(
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

        runtime = current_runtime()
        initializer = configure_worker_logging if runtime else None
        initargs = (runtime.queue, runtime.invocation) if runtime else ()
        remaining = iter(items)
        stop_scheduling = False
        with ProcessPoolExecutor(
            max_workers=workers, initializer=initializer, initargs=initargs
        ) as executor:
            active = {}
            for item in items[:workers]:
                next(remaining)
                active[executor.submit(fn, item)] = key_fn(item)
            while active:
                done, _ = wait(active, return_when=FIRST_COMPLETED)
                for future in done:
                    key = active.pop(future)
                    try:
                        results[key] = future.result()
                    except Exception as error:
                        errors[key] = error
                        logging.getLogger(__name__).warning(
                            "Task %s failed (%s); details retained for the workflow summary",
                            key,
                            type(error).__name__,
                        )
                        if isinstance(error, (ProviderError, StorageError, ArtifactError)):
                            stop_scheduling = True
                if not stop_scheduling:
                    for _ in done:
                        item = next(remaining, None)
                        if item is not None:
                            active[executor.submit(fn, item)] = key_fn(item)

        if errors:
            raise OrchestrationError(errors, results) from next(iter(errors.values()))

        return results
