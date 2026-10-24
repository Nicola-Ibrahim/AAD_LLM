"""Public evolution module: process-local root, operation scopes, direct use-case calls."""

import os
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Never

import pandas as pd
from dishka import Container, make_container

from evolution.application.campaign.models import CampaignResults
from evolution.application.campaign.run import SynthesisCampaignCoordinator
from evolution.application.synthesis_config import (
    NoiseConditionConfig,
    ProblemTarget,
    SynthesisModeConfig,
)
from evolution.infra.di import EvolutionProvider
from evolution.infra.llm.client import LLMClient
from shared.infra.di import SharedProvider


class EvolutionModule:
    """Reusable notebook/CLI/API entry point; the caller owns startup and shutdown."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._container = make_container(
            SharedProvider(), EvolutionProvider(), context={LLMClient: llm_client}
        )
        self._owner_pid = os.getpid()
        self._closed = False

    def audit_matrix(
        self,
        *,
        problem_targets: list[ProblemTarget],
        noise_conditions: list[NoiseConditionConfig],
        synthesis_modes: list[SynthesisModeConfig],
        iterations: int,
        budget: int,
        timeout_seconds: float,
        runs_per_config: int,
        auto_resume: bool,
        skip_completed: bool,
        retry_failed_synthesis: bool,
    ) -> tuple[pd.DataFrame, dict[str, object]]:
        """Delegate within a fresh operation scope; return detached results."""
        with self._operation({}) as scope:
            return scope.get(SynthesisCampaignCoordinator).audit_matrix(
                problem_targets=problem_targets,
                noise_conditions=noise_conditions,
                synthesis_modes=synthesis_modes,
                iterations=iterations,
                budget=budget,
                timeout_seconds=timeout_seconds,
                runs_per_config=runs_per_config,
                auto_resume=auto_resume,
                skip_completed=skip_completed,
                retry_failed_synthesis=retry_failed_synthesis,
            )

    def run_campaign(
        self,
        *,
        problem_targets: list[ProblemTarget],
        noise_conditions: list[NoiseConditionConfig],
        synthesis_modes: list[SynthesisModeConfig],
        iterations: int,
        budget: int,
        timeout_seconds: float,
        runs_per_config: int,
        auto_resume: bool,
        skip_completed: bool,
        retry_failed_synthesis: bool,
        verbose: bool = True,
        recover: bool = False,
        rerun_experiment_ids: Sequence[int] = (),
        resume_experiment_ids: Sequence[int] = (),
    ) -> CampaignResults:
        """Delegate within a fresh operation scope; return detached results."""
        with self._operation({}) as scope:
            return scope.get(SynthesisCampaignCoordinator).run_campaign(
                problem_targets=problem_targets,
                noise_conditions=noise_conditions,
                synthesis_modes=synthesis_modes,
                iterations=iterations,
                budget=budget,
                timeout_seconds=timeout_seconds,
                runs_per_config=runs_per_config,
                auto_resume=auto_resume,
                skip_completed=skip_completed,
                retry_failed_synthesis=retry_failed_synthesis,
                verbose=verbose,
                recover=recover,
                rerun_experiment_ids=rerun_experiment_ids,
                resume_experiment_ids=resume_experiment_ids,
            )

    def close(self) -> None:
        """Close the module root once, in its owning process."""
        if self._closed or os.getpid() != self._owner_pid:
            return
        self._closed = True
        self._container.close()

    @contextmanager
    def _operation(self, context: dict[type, object]) -> Iterator[Container]:
        if os.getpid() != self._owner_pid:
            raise RuntimeError("Modules are process-local; create one in the current process.")
        if self._closed:
            raise RuntimeError("Module is closed. Create a new module before calling operations.")
        with self._container(context=context) as scope:
            yield scope

    def __getstate__(self) -> Never:
        raise TypeError("Module containers must not be serialized into worker tasks.")
