"""Resource ownership for long-lived synchronous workflows and interactive hosts."""

import atexit
import logging
import os
from contextlib import ExitStack
from typing import TypeVar

from dishka import Provider

from shared.infra import di
from shared.infra.logging.runtime import start_logging

T = TypeVar("T")


class WorkflowScope:
    """Keep Dishka resources alive across interactive cells or a synchronous job.

    The host resolves services during setup and calls them normally afterward.
    Close before replacing the workflow; normal interpreter shutdown also closes it.
    Services must not outlive this scope or be passed to another process.
    """

    def __init__(
        self,
        *providers: Provider,
        context: dict[type, object],
        request_context: dict[type, object],
    ) -> None:
        self._owner_pid = os.getpid()
        self._closed = False
        self._resources = ExitStack()
        workflow = providers[0].__class__.__module__.split(".")[0] if providers else "workflow"
        self.logging = start_logging(workflow)
        self._resources.callback(self.logging.close)
        try:
            with self.logging.operation("setup"):
                logging.getLogger(__name__).info(
                    "Diagnostic log: %s", self.logging.path, extra={"progress": True}
                )
                self._services = self._resources.enter_context(
                    di.container_scope(*providers, context=context, request_context=request_context)
                )
        except BaseException:
            self._close_after_failure()
            raise
        atexit.register(self.close)

    def get(self, dependency: type[T]) -> T:
        """Resolve a setup dependency, closing resources if construction fails."""
        if os.getpid() != self._owner_pid:
            raise RuntimeError("Create a process-local scope before resolving services.")
        if self._closed:
            raise RuntimeError("This workflow scope is closed; rerun setup.")
        try:
            with self.logging.operation(f"resolve {dependency.__name__}"):
                return self._services.get(dependency)
        except BaseException:
            self._close_after_failure()
            raise

    def _close_after_failure(self) -> None:
        """Preserve the setup/resolve error even if resource teardown also fails."""
        try:
            self.close()
        except Exception:
            logging.getLogger(__name__).warning(
                "Cleanup failed; preserving the original error", exc_info=True
            )

    def close(self) -> None:
        """Release resources once, only in the process that created them."""
        if os.getpid() != self._owner_pid or self._closed:
            return
        self._closed = True
        atexit.unregister(self.close)
        self._resources.close()
