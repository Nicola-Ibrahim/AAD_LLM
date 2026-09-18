from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from evolution.domain.enums import NoiseEnvironment, PromptStrategy, SynthesisMode
from evolution.domain.interfaces import BaseProblem


class ModeTemplate(StrEnum):
    """Jinja template filenames for synthesis modes."""

    CLEAN = "modes/clean.j2"
    NOISY = "modes/noisy.j2"
    IMPLICIT = "modes/implicit.j2"


MODE_TEMPLATE_MAP: dict[tuple[SynthesisMode, NoiseEnvironment], ModeTemplate] = {
    (SynthesisMode.EXPLICIT, NoiseEnvironment.CLEAN): ModeTemplate.CLEAN,
    (SynthesisMode.EXPLICIT, NoiseEnvironment.NOISY): ModeTemplate.NOISY,
    (SynthesisMode.IMPLICIT, NoiseEnvironment.CLEAN): ModeTemplate.IMPLICIT,
    (SynthesisMode.IMPLICIT, NoiseEnvironment.NOISY): ModeTemplate.IMPLICIT,
}

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


@dataclass(frozen=True, slots=True)
class SynthesisPrompts:
    """Bundle of prompt components required by evolutionary synthesis engines."""

    task: str
    example: str
    format: str


def build_task_prompt(
    problem: BaseProblem,
    mode: SynthesisMode = SynthesisMode.EXPLICIT,
    strategy: PromptStrategy = PromptStrategy.BASELINE,
    noise_std: float = 0.0,
    noise_environment: NoiseEnvironment = NoiseEnvironment.CLEAN,
    budget_hint: int | None = None,
) -> str:
    """Constructs the structured task prompt based on a BaseProblem instance and domain enums.

    Args:
        problem: BaseProblem instance (extracts problem_id, dim, bounds, noise_std). Never None.
        mode: SynthesisMode (Level 1: EXPLICIT or IMPLICIT). Never None.
        strategy: PromptStrategy (Level 3: BASELINE, GUIDED, THINKING, VECTORIZATION). Never None.
        noise_std: Numerical noise std. Used internally to derive NoiseEnvironment if > 0.
        noise_environment: Optional explicit NoiseEnvironment (Level 2: CLEAN or NOISY).
        budget_hint: Function evaluation budget hint.
    """
    effective_noise_std = (
        noise_std if noise_std > 0.0 else problem.noise_std
    )
    env = (
        NoiseEnvironment.from_std(effective_noise_std)
        if effective_noise_std > 0.0
        else noise_environment
    )
    template_name = MODE_TEMPLATE_MAP[(mode, env)]
    mode_prompt = _jinja_env.get_template(template_name.value).render().strip()

    strat_template = f"strategies/{strategy}.j2"
    strategy_prompt = (
        _jinja_env.get_template(strat_template).render().strip()
        if (_TEMPLATES_DIR / strat_template).exists()
        else ""
    )

    return _jinja_env.get_template("layout.j2").render(
        problem_id=problem.problem_id,
        dimension=problem.dim,
        lower_bound=problem.lower_bound.tolist(),
        upper_bound=problem.upper_bound.tolist(),
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


def build_synthesis_prompts(
    problem: BaseProblem,
    mode: SynthesisMode = SynthesisMode.EXPLICIT,
    strategy: PromptStrategy = PromptStrategy.BASELINE,
    noise_std: float = 0.0,
    noise_environment: NoiseEnvironment = NoiseEnvironment.CLEAN,
    budget_hint: int | None = None,
) -> SynthesisPrompts:
    """Constructs the complete prompt suite (task, example, format) for an evolutionary synthesis run."""
    task = build_task_prompt(
        problem=problem,
        mode=mode,
        strategy=strategy,
        noise_std=noise_std,
        noise_environment=noise_environment,
        budget_hint=budget_hint,
    )
    return SynthesisPrompts(
        task=task,
        example=build_example_prompt(),
        format=build_format_prompt(),
    )


def assemble_full_prompt(
    prompts: SynthesisPrompts | str,
    format_prompt: str = "",
    example_prompt: str = "",
) -> str:
    """Formats and concatenates the complete prompt components as presented to the LLM."""
    if isinstance(prompts, SynthesisPrompts):
        task_str = prompts.task
        fmt_str = prompts.format
        ex_str = prompts.example
    else:
        task_str = prompts
        fmt_str = format_prompt or build_format_prompt()
        ex_str = example_prompt or build_example_prompt()

    separator = "#" * 80
    return (
        f"{separator}\n"
        f"# 1. TASK PROMPT (Problem Description & Strategy Guidance)\n"
        f"{separator}\n"
        f"{task_str}\n\n"
        f"{separator}\n"
        f"# 2. OUTPUT FORMAT RULES\n"
        f"{separator}\n"
        f"{fmt_str}\n\n"
        f"{separator}\n"
        f"# 3. CODE SKELETON EXAMPLE\n"
        f"{separator}\n"
        f"{ex_str}\n"
    )
