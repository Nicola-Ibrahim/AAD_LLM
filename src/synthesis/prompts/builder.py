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
    budget_hint: int | None = None,
) -> str:
    """Constructs the structured task prompt based on explicit problem parameters, ProblemMode enum, and prompt strategy."""
    mode_str = (ProblemMode(mode) if isinstance(mode, str) else mode).value
    strategy_str = (PromptStrategy(strategy) if isinstance(strategy, str) else strategy).value

    problem_nature = _jinja_env.get_template(f"modes/{mode_str}.j2").render()

    strat_template = f"strategies/{mode_str}/{strategy_str}.j2"
    strategy_guidance = (
        _jinja_env.get_template(strat_template).render()
        if (_TEMPLATES_DIR / strat_template).exists()
        else ""
    )

    return _jinja_env.get_template("layout.j2").render(
        problem_id=problem_id,
        dim=dim,
        lower_bound=lower_bound.tolist(),
        upper_bound=upper_bound.tolist(),
        budget_hint=budget_hint,
        problem_nature=problem_nature.strip(),
        strategy_guidance=strategy_guidance.strip(),
        is_noisy=(mode_str == "noisy"),
    )


def build_example_prompt() -> str:
    """Renders the standard code skeleton prompt."""
    return _jinja_env.get_template("shared/example.j2").render()


def build_format_prompt() -> str:
    """Renders the strict output format and rule checking prompt."""
    return _jinja_env.get_template("shared/format.j2").render()


EXAMPLE_PROMPT: str = build_example_prompt()
FORMAT_PROMPT: str = build_format_prompt()
