from enum import StrEnum
from pathlib import Path

import numpy as np
from jinja2 import Environment, FileSystemLoader, select_autoescape

from domain.enums import ProblemMode


class PromptStrategy(StrEnum):
    BASELINE = "baseline"
    THINKING = "thinking"
    VECTORIZATION = "vectorization"
    GUIDED = "guided"


_TEMPLATES_DIR = Path(__file__).parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape([]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def build_task_prompt(
    problem_id: int,
    dim: int,
    lower_bound: np.ndarray,
    upper_bound: np.ndarray,
    mode: ProblemMode | str = ProblemMode.CLEAN,
    strategy: PromptStrategy | str = PromptStrategy.BASELINE,
) -> str:
    """Constructs the structured task prompt based on explicit problem parameters, ProblemMode enum, and prompt strategy."""
    mode_enum = ProblemMode(mode) if isinstance(mode, str) else mode
    strategy_enum = PromptStrategy(strategy) if isinstance(strategy, str) else strategy
    template_name = "task_noisy.j2" if mode_enum == ProblemMode.NOISY else "task_clean.j2"
    return _jinja_env.get_template(template_name).render(
        problem_id=problem_id,
        dim=dim,
        lower_bound=lower_bound.tolist(),
        upper_bound=upper_bound.tolist(),
        mode=mode_enum,
        strategy=strategy_enum,
    )
