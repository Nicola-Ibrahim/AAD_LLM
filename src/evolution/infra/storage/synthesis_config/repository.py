"""Synthesis Configuration Read Repository (Pure I/O & TOML Parsing).

Encapsulates reading, parsing, and resolving synthesis.toml / experiments.toml
for evolutionary synthesis search spaces and execution parameters.
"""

import os
import tomllib
from pathlib import Path
from typing import cast

from evolution.application.synthesis_config import (
    MatrixCondition,
    NoiseConditionConfig,
    ProblemTarget,
    SynthesisConfig,
    SynthesisModeConfig,
)
from evolution.domain.enums import PromptStrategy, SynthesisMode
from shared.config import CONFIGS_DIR
from shared.domain.noise_model import NoiseModelEnum


def _table(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


def _items(value: object, default: list[object]) -> list[object]:
    return value if isinstance(value, list) else default


def _number(value: object, default: int | float) -> int | float:
    if isinstance(value, (int, float, str)):
        return float(value) if isinstance(default, float) else int(value)
    return default


def _text(value: object, default: str) -> str:
    return value if isinstance(value, str) else default


class SynthesisConfigRepository:
    """Infrastructure repository for reading and parsing synthesis.toml into SynthesisConfig."""

    def __init__(
        self,
        config_path: Path = CONFIGS_DIR / "synthesis.toml",
    ) -> None:
        self.config_path = config_path

    def load_config(self) -> SynthesisConfig:
        """Loads and parses the synthesis configuration into strongly typed SynthesisConfig."""
        cfg: dict[str, object] = {}
        if self.config_path.exists():
            with open(self.config_path, "rb") as f:
                cfg = cast(dict[str, object], tomllib.load(f))

        matrix_cfg = _table(cfg.get("matrix", {}))
        evolution_cfg = _table(cfg.get("evolution", {}))
        exec_meta = _table(cfg.get("execution", {}))

        # 1. Parse prompt strategies & synthesis modes
        default_strats_raw = _items(
            matrix_cfg.get("prompt_strategies"),
            ["baseline", "thinking", "vectorization", "guided"],
        )
        if isinstance(matrix_cfg.get("prompt_strategies"), str):
            default_strats_raw = [matrix_cfg["prompt_strategies"]]
        if isinstance(default_strats_raw, str):
            default_strats_raw = [default_strats_raw]
        default_strategies = [
            PromptStrategy(_text(s, "baseline").lower()) for s in default_strats_raw
        ]

        raw_synthesis_modes = matrix_cfg.get("synthesis_modes")
        if isinstance(raw_synthesis_modes, str):
            raw_synthesis_modes = [raw_synthesis_modes]
        raw_synthesis_modes = _items(raw_synthesis_modes, [])
        if raw_synthesis_modes:
            parsed_modes: list[SynthesisModeConfig] = []
            for item in raw_synthesis_modes:
                mode_item = _table(item)
                if mode_item:
                    m_enum = SynthesisMode(_text(mode_item.get("mode"), "").lower())
                    strats = [
                        PromptStrategy(_text(s, "baseline").lower())
                        for s in _items(mode_item.get("strategies"), list(default_strategies))
                    ]
                    parsed_modes.append(SynthesisModeConfig(mode=m_enum, strategies=strats))
                else:
                    m_enum = SynthesisMode(_text(item, "explicit").lower())
                    parsed_modes.append(
                        SynthesisModeConfig(mode=m_enum, strategies=list(default_strategies))
                    )
            synthesis_modes = parsed_modes
        else:
            raw_single_mode = _text(
                matrix_cfg.get("synthesis_mode") or evolution_cfg.get("synthesis_mode"), ""
            )
            if raw_single_mode:
                synthesis_modes = [
                    SynthesisModeConfig(
                        mode=SynthesisMode(str(raw_single_mode).lower()),
                        strategies=list(default_strategies),
                    )
                ]
            else:
                synthesis_modes = [
                    SynthesisModeConfig(
                        mode=SynthesisMode.EXPLICIT, strategies=list(default_strategies)
                    ),
                    SynthesisModeConfig(
                        mode=SynthesisMode.IMPLICIT, strategies=list(default_strategies)
                    ),
                ]

        # 2. Parse noise conditions and associate applicable modes upfront
        raw_noise_conditions = matrix_cfg.get("noise_conditions")
        default_model_str = _text(matrix_cfg.get("noise_model"), "heteroscedastic")
        default_model = NoiseModelEnum(default_model_str.lower())

        if isinstance(raw_noise_conditions, list) and raw_noise_conditions:
            raw_cond_tuples = [
                (
                    float(_number(_table(c).get("std"), 0.0)),
                    NoiseModelEnum(
                        _text(
                            _table(c).get("noise_model")
                            or _table(c).get(
                                "model",
                                "none"
                                if float(_number(_table(c).get("std"), 0.0)) == 0.0
                                else default_model_str,
                            ),
                            default_model_str,
                        ).lower()
                    ),
                    _text(_table(c).get("mode"), "").lower() or None,
                )
                for c in raw_noise_conditions
                if isinstance(c, dict)
            ]
        else:
            noise_stds_raw = [
                float(_number(s, 0.0)) for s in _items(matrix_cfg.get("noise_stds"), [0.0, 0.05])
            ]
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
                    matching_modes = [
                        SynthesisModeConfig(mode=target_enum, strategies=list(default_strategies))
                    ]
                applicable_modes = matching_modes
            else:
                applicable_modes = synthesis_modes

            noise_conditions.append(
                NoiseConditionConfig(
                    std=std,
                    noise_model=model,
                    mode=explicit_mode,
                    modes=applicable_modes,
                )
            )

        # 3. Parse problem targets
        raw_problem_targets = matrix_cfg.get("problem_targets")
        if isinstance(raw_problem_targets, list) and raw_problem_targets:
            problem_targets = [
                ProblemTarget(
                    id=int(_number(target.get("id"), 1)),
                    dimensions=[
                        int(_number(dim, 2)) for dim in _items(target.get("dimensions"), [2, 3, 5])
                    ],
                )
                for t in raw_problem_targets
                if isinstance(t, dict)
                for target in [_table(t)]
            ]
        else:
            default_p_ids = [
                int(_number(problem_id, 1))
                for problem_id in _items(matrix_cfg.get("problem_ids"), [1, 8, 11, 15, 21])
            ]
            default_dims = [
                int(_number(dim, 2)) for dim in _items(matrix_cfg.get("dimensions"), [2, 3, 5])
            ]
            problem_targets = [
                ProblemTarget(id=p, dimensions=list(default_dims)) for p in default_p_ids
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
                                    noise_model=noise_cond.noise_model,
                                    strategy=strat,
                                )
                            )

        # 5. Assemble SynthesisConfig
        num_workers = int(_number(exec_meta.get("max_workers"), 0)) or os.cpu_count() or 8
        target_ids_raw = exec_meta.get("target_experiment_ids")
        target_ids: list[int] = (
            [int(_number(i, 0)) for i in target_ids_raw] if isinstance(target_ids_raw, list) else []
        )

        timeout_sec = float(
            _number(
                evolution_cfg.get(
                    "timeout_seconds",
                    evolution_cfg.get("eval_timeout_seconds", 30.0),
                ),
                30.0,
            )
        )

        return SynthesisConfig(
            problem_targets=problem_targets,
            noise_conditions=noise_conditions,
            synthesis_modes=synthesis_modes,
            matrix_conditions=matrix_conditions,
            budget=int(_number(evolution_cfg.get("budget"), 1_000_000)),
            timeout_seconds=timeout_sec,
            iterations=int(_number(evolution_cfg.get("iterations"), 10)),
            stagnation_threshold=int(_number(evolution_cfg.get("stagnation_threshold"), 3)),
            convergence_threshold=float(_number(evolution_cfg.get("convergence_threshold"), 1e-6)),
            runs_per_config=int(_number(evolution_cfg.get("runs_per_config"), 1)),
            num_processes=num_workers,
            auto_resume=bool(exec_meta.get("auto_resume", True)),
            skip_completed=bool(exec_meta.get("skip_completed", True)),
            retry_failed_synthesis=bool(exec_meta.get("retry_failed_synthesis", True)),
            only_incomplete=bool(exec_meta.get("only_incomplete", False)),
            target_exp_ids=target_ids,
            rerun_experiment_ids=[
                int(_number(identifier, 0))
                for identifier in _items(exec_meta.get("rerun_experiment_ids"), [])
            ],
            rerun_repeats=int(_number(exec_meta.get("rerun_repeats"), 1)),
            name=_text(evolution_cfg.get("name"), "bbob_comprehensive_matrix"),
            noise_model=default_model,
        )
