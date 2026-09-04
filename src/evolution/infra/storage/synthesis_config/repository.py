"""Synthesis Configuration Read Repository (Pure I/O & TOML Parsing).

Encapsulates reading, parsing, and resolving synthesis.toml / experiments.toml
for evolutionary synthesis search spaces and execution parameters.
"""

import os
from pathlib import Path
from typing import Any
import tomllib

from shared.config import CONFIGS_DIR
from evolution.domain.enums import NoiseModelEnum, PromptStrategy, SynthesisMode
from evolution.infra.storage.synthesis_config.models import (
    MatrixCondition,
    NoiseConditionConfig,
    ProblemTarget,
    SynthesisConfig,
    SynthesisModeConfig,
)


class SynthesisConfigRepository:
    """Infrastructure repository for reading and parsing synthesis.toml into SynthesisConfig."""

    def __init__(
        self,
        config_path: Path = CONFIGS_DIR / "synthesis.toml",
    ):
        self.config_path = config_path

    def load_config(self) -> SynthesisConfig:
        """Loads and parses the synthesis configuration into strongly typed SynthesisConfig."""
        cfg: dict[str, Any] = {}
        if self.config_path.exists():
            with open(self.config_path, "rb") as f:
                cfg = tomllib.load(f)

        matrix_cfg = cfg.get("matrix", {})
        evolution_cfg = cfg.get("evolution", {})
        exec_meta = cfg.get("execution", {})

        # 1. Parse prompt strategies & synthesis modes
        default_strats_raw = matrix_cfg.get(
            "prompt_strategies", ["baseline", "thinking", "vectorization", "guided"]
        )
        if isinstance(default_strats_raw, str):
            default_strats_raw = [default_strats_raw]
        default_strategies = [
            PromptStrategy(s.lower()) if isinstance(s, str) else s
            for s in default_strats_raw
        ]

        raw_synthesis_modes = matrix_cfg.get("synthesis_modes")
        if raw_synthesis_modes:
            if isinstance(raw_synthesis_modes, str):
                raw_synthesis_modes = [raw_synthesis_modes]
            parsed_modes: list[SynthesisModeConfig] = []
            for item in raw_synthesis_modes:
                if isinstance(item, dict):
                    m_enum = SynthesisMode(str(item.get("mode", "")).lower())
                    strats = [
                        PromptStrategy(str(s).lower()) if isinstance(s, str) else s
                        for s in item.get("strategies", default_strategies)
                    ]
                    parsed_modes.append(SynthesisModeConfig(mode=m_enum, strategies=strats))
                else:
                    m_enum = SynthesisMode(str(item).lower())
                    parsed_modes.append(
                        SynthesisModeConfig(mode=m_enum, strategies=list(default_strategies))
                    )
            synthesis_modes = parsed_modes
        else:
            raw_single_mode = matrix_cfg.get("synthesis_mode") or evolution_cfg.get("synthesis_mode")
            if raw_single_mode:
                synthesis_modes = [
                    SynthesisModeConfig(
                        mode=SynthesisMode(str(raw_single_mode).lower()),
                        strategies=list(default_strategies),
                    )
                ]
            else:
                synthesis_modes = [
                    SynthesisModeConfig(mode=SynthesisMode.CLEAN, strategies=list(default_strategies)),
                    SynthesisModeConfig(mode=SynthesisMode.NOISY, strategies=list(default_strategies)),
                    SynthesisModeConfig(mode=SynthesisMode.IMPLICIT, strategies=list(default_strategies)),
                ]

        # 2. Parse noise conditions and associate applicable modes upfront
        raw_noise_conditions = matrix_cfg.get("noise_conditions")
        default_model_str = matrix_cfg.get("noise_model", "heteroscedastic")
        default_model = NoiseModelEnum(default_model_str.lower())

        if raw_noise_conditions:
            raw_cond_tuples = [
                (
                    float(c["std"]),
                    NoiseModelEnum(
                        str(c.get("model", "none" if float(c["std"]) == 0.0 else default_model_str)).lower()
                    ),
                    str(c["mode"]).lower() if c.get("mode") else None,
                )
                for c in raw_noise_conditions
            ]
        else:
            noise_stds_raw = [float(s) for s in matrix_cfg.get("noise_stds", [0.0, 0.05])]
            raw_cond_tuples = [
                (s, NoiseModelEnum.NONE if s == 0.0 else default_model, None)
                for s in noise_stds_raw
            ]

        noise_conditions: list[NoiseConditionConfig] = []
        for std, model, explicit_mode in raw_cond_tuples:
            if explicit_mode:
                target_enum = SynthesisMode(explicit_mode.lower())
                matching_modes = [m for m in synthesis_modes if m.mode == target_enum]
                if not matching_modes:
                    matching_modes = [SynthesisModeConfig(mode=target_enum, strategies=list(default_strategies))]
                applicable_modes = matching_modes
            elif std == 0.0:
                applicable_modes = [m for m in synthesis_modes if m.mode == SynthesisMode.CLEAN]
            else:
                applicable_modes = [
                    m for m in synthesis_modes if m.mode in (SynthesisMode.NOISY, SynthesisMode.IMPLICIT)
                ]

            noise_conditions.append(
                NoiseConditionConfig(
                    std=std,
                    model=model,
                    mode=explicit_mode,
                    modes=applicable_modes,
                )
            )

        # 3. Parse problem targets
        raw_problem_targets = matrix_cfg.get("problem_targets")
        if raw_problem_targets:
            problem_targets = [
                ProblemTarget(
                    id=int(t["id"]),
                    dimensions=[int(d) for d in t.get("dimensions", [2, 3, 5])],
                )
                for t in raw_problem_targets
            ]
        else:
            default_p_ids = [int(p) for p in matrix_cfg.get("problem_ids", [1, 8, 11, 15, 21])]
            default_dims = [int(d) for d in matrix_cfg.get("dimensions", [2, 3, 5])]
            problem_targets = [
                ProblemTarget(id=p, dimensions=list(default_dims))
                for p in default_p_ids
            ]

        # 4. Pre-compute complete search matrix conditions
        matrix_conditions: list[MatrixCondition] = []
        for target in problem_targets:
            for dim in target.dimensions:
                for noise_cond in noise_conditions:
                    for mode_cfg in noise_cond.modes:
                        for strat in mode_cfg.strategies:
                            matrix_conditions.append(
                                MatrixCondition(
                                    problem_id=target.id,
                                    dim=dim,
                                    mode=mode_cfg.mode,
                                    noise_std=noise_cond.std,
                                    noise_model=noise_cond.model,
                                    strategy=strat,
                                )
                            )

        # 5. Assemble SynthesisConfig
        num_workers = int(exec_meta.get("max_workers", 0)) or os.cpu_count() or 8
        target_ids = exec_meta.get("target_experiment_ids")
        if target_ids is not None:
            target_ids = [int(i) for i in target_ids]

        return SynthesisConfig(
            problem_targets=problem_targets,
            noise_conditions=noise_conditions,
            synthesis_modes=synthesis_modes,
            matrix_conditions=matrix_conditions,
            budget=int(evolution_cfg.get("budget", 1_000_000)),
            iterations=int(evolution_cfg.get("iterations", 10)),
            runs_per_config=int(evolution_cfg.get("runs_per_config", 1)),
            num_processes=num_workers,
            auto_resume=bool(exec_meta.get("auto_resume", True)),
            skip_completed=bool(exec_meta.get("skip_completed", True)),
            retry_failed_synthesis=bool(exec_meta.get("retry_failed_synthesis", True)),
            only_incomplete=bool(exec_meta.get("only_incomplete", False)),
            target_exp_ids=target_ids,
            name=str(evolution_cfg.get("name", "bbob_comprehensive_matrix")),
            noise_model=default_model,
            matrix=matrix_cfg,
            evolution=evolution_cfg,
            execution=exec_meta,
        )


