"""Narrow LLaMEA hooks: preserve its algorithm, surface terminal external failures."""

import logging
import sys

from llamea import LLaMEA, Solution

from evolution.infra.llm.client import LLMClient


class FailureAwareLLaMEA(LLaMEA):
    def _check_dependencies(self) -> None:
        if isinstance(self.llm, LLMClient):
            self.llm.raise_if_failed()
        self.f.raise_if_failed()

    def initialize_single(self) -> Solution:
        result = super().initialize_single()
        self._check_dependencies()
        return result

    def evolve_solution(self, individual: Solution) -> Solution:
        result = super().evolve_solution(individual)
        self._check_dependencies()
        return result

    def logevent(self, event: str) -> None:
        # LLaMEA passes rendered exception chains here inside its catches. Terminal
        # dependency errors are surfaced by the guards; candidate errors already
        # have scientific diagnostics. Do not duplicate unsafe vendor bodies.
        if sys.exception() is None:
            logging.getLogger(__name__).debug("%s", event)
