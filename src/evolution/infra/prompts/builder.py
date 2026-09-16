from functools import lru_cache
from pathlib import Path

import numpy as np
from jinja2 import Environment, FileSystemLoader, select_autoescape

from evolution.domain.enums import PromptStrategy, SynthesisMode


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
    mode: SynthesisMode = SynthesisMode.CLEAN,
    strategy: PromptStrategy = PromptStrategy.BASELINE,
    budget_hint: int | None = None,
) -> str:
    """Constructs the structured task prompt based on explicit problem parameters, SynthesisMode enum, and prompt strategy."""
    mode_prompt = _jinja_env.get_template(f"modes/{mode}.j2").render().strip()

    strat_template = f"strategies/{strategy}.j2"
    strategy_prompt = (
        _jinja_env.get_template(strat_template).render().strip()
        if (_TEMPLATES_DIR / strat_template).exists()
        else ""
    )

    return _jinja_env.get_template("layout.j2").render(
        problem_id=problem_id,
        dimension=dim,
        lower_bound=lower_bound.tolist(),
        upper_bound=upper_bound.tolist(),
        budget=budget_hint,
        mode_prompt=mode_prompt,
        strategy_prompt=strategy_prompt,
    )


@lru_cache(maxsize=1)
def build_example_prompt() -> str:
    """Renders the standard code skeleton prompt."""
    return _jinja_env.get_template("shared/example.j2").render()


@lru_cache(maxsize=1)
def build_format_prompt() -> str:
    """Renders the strict output format and rule checking prompt."""
    return _jinja_env.get_template("shared/format.j2").render()
