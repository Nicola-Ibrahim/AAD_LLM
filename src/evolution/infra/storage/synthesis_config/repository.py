"""Load validated TOML and resolve the typed synthesis experiment matrix."""

import os
import tomllib
from pathlib import Path

from evolution.application.synthesis_config import (
    MatrixCondition,
    NoiseConditionConfig,
    ProblemTarget,
    SynthesisConfig,
    SynthesisModeConfig,
)
from evolution.domain.enums import SynthesisMode
from evolution.infra.storage.synthesis_config.toml_models import NoiseConditionToml, SynthesisToml
from shared.config import CONFIGS_DIR
from shared.domain.noise_model import NoiseModelEnum


class SynthesisConfigRepository:
    """Validate external configuration once; return application-owned typed data."""

    def __init__(self, config_path: Path = CONFIGS_DIR / "synthesis.toml") -> None:
        self.config_path = config_path

    def load_config(self) -> SynthesisConfig:
        if self.config_path.exists():
            with self.config_path.open("rb") as stream:
                source = SynthesisToml(**tomllib.load(stream))
        else:
            source = SynthesisToml()
        matrix, evolution, execution = source.matrix, source.evolution, source.execution

        synthesis_modes: list[SynthesisModeConfig] = []
        for item in matrix.synthesis_modes:
            if isinstance(item, SynthesisMode):
                mode, strategies = item, matrix.prompt_strategies
            else:
                mode = item.mode
                strategies = (
                    matrix.prompt_strategies if item.strategies is None else item.strategies
                )
            synthesis_modes.append(SynthesisModeConfig(mode=mode, strategies=strategies))
        if not synthesis_modes:
            selected_mode = matrix.synthesis_mode or evolution.synthesis_mode
            modes = [selected_mode] if selected_mode is not None else list(SynthesisMode)
            synthesis_modes = [
                SynthesisModeConfig(mode=mode, strategies=matrix.prompt_strategies)
                for mode in modes
            ]

        input_noise = matrix.noise_conditions or [
            NoiseConditionToml(std=std) for std in matrix.noise_stds
        ]
        noise_conditions: list[NoiseConditionConfig] = []
        for condition in input_noise:
            noise_model = (
                condition.noise_model
                or condition.model
                or (NoiseModelEnum.NONE if condition.std == 0.0 else matrix.noise_model)
            )
            applicable_modes = synthesis_modes
            if condition.mode is not None:
                applicable_modes = [mode for mode in synthesis_modes if mode.mode == condition.mode]
                if not applicable_modes:
                    applicable_modes = [
                        SynthesisModeConfig(
                            mode=condition.mode, strategies=matrix.prompt_strategies
                        )
                    ]
            noise_conditions.append(
                NoiseConditionConfig(
                    std=condition.std,
                    noise_model=noise_model,
                    mode=condition.mode,
                    modes=applicable_modes,
                )
            )

        if matrix.problem_targets:
            problem_targets = [
                ProblemTarget(id=target.id, dimensions=target.dimensions)
                for target in matrix.problem_targets
            ]
        else:
            problem_targets = [
                ProblemTarget(id=problem_id, dimensions=matrix.dimensions)
                for problem_id in matrix.problem_ids
            ]
        matrix_conditions = [
            MatrixCondition(
                problem_id=target.id,
                dim=dim,
                mode=mode.mode,
                noise_std=noise.std,
                noise_model=noise.noise_model,
                strategy=strategy,
            )
            for target in problem_targets
            for dim in target.dimensions
            for noise in noise_conditions
            for mode in noise.modes
            for strategy in mode.strategies
        ]
        return SynthesisConfig(
            problem_targets=problem_targets,
            noise_conditions=noise_conditions,
            synthesis_modes=synthesis_modes,
            matrix_conditions=matrix_conditions,
            budget=evolution.budget,
            timeout_seconds=(
                evolution.eval_timeout_seconds
                if evolution.timeout_seconds is None
                else evolution.timeout_seconds
            ),
            iterations=evolution.iterations,
            stagnation_threshold=evolution.stagnation_threshold,
            convergence_threshold=evolution.convergence_threshold,
            runs_per_config=evolution.runs_per_config,
            num_processes=execution.max_workers or os.cpu_count() or 8,
            auto_resume=execution.auto_resume,
            skip_completed=execution.skip_completed,
            retry_failed_synthesis=execution.retry_failed_synthesis,
            only_incomplete=execution.only_incomplete,
            name=evolution.name,
            noise_model=matrix.noise_model,
        )
