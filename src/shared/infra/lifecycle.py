"""Resource ownership for long-lived synchronous workflows and interactive hosts."""

import atexit
import os
from contextlib import ExitStack
from typing import TypeVar

from dishka import Provider

from shared.infra import di

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
        try:
            self._services = self._resources.enter_context(
                di.container_scope(*providers, context=context, request_context=request_context)
            )
        except BaseException:
            self.close()
            raise
        atexit.register(self.close)

    def get(self, dependency: type[T]) -> T:
        """Resolve a setup dependency, closing resources if construction fails."""
        if os.getpid() != self._owner_pid:
            raise RuntimeError("Create a process-local scope before resolving services.")
        if self._closed:
            raise RuntimeError("This workflow scope is closed; rerun setup.")
        try:
            return self._services.get(dependency)
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        """Release resources once, only in the process that created them."""
        if os.getpid() != self._owner_pid or self._closed:
            return
        self._closed = True
        atexit.unregister(self.close)
        self._resources.close()
