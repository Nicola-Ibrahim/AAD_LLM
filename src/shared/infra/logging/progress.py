"""Scientific progress records use host handlers and instance-local verbosity."""

import logging
from contextlib import AbstractContextManager

from shared.application.diagnostics import report_operation
from shared.infra.logging.runtime import current_runtime


class ProgressLogger(logging.LoggerAdapter):
    def __init__(self, name: str, verbose: bool) -> None:
        super().__init__(logging.getLogger(name), {"progress": True})
        self.verbose = verbose
        self.runtime = current_runtime()

    def isEnabledFor(self, level: int) -> bool:
        return (self.verbose or level >= logging.WARNING) and super().isEnabledFor(level)

    def operation(self, name: str) -> AbstractContextManager[None]:
        if self.runtime is not None:
            return self.runtime.operation(name)
        return report_operation(self.logger, name)
