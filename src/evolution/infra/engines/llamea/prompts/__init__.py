"""Jinja2-based prompt templates and prompt building infrastructure for evolutionary search."""

from .builder import (
    MODE_TEMPLATE_MAP,
    ModeTemplate,
    PromptStrategy,
    SynthesisPrompts,
    assemble_full_prompt,
    build_example_prompt,
    build_format_prompt,
    build_synthesis_prompts,
    build_task_prompt,
)
from .feedback import (
    META_FEEDBACK_DIVERSITY_INJECTION,
    NOISY_PROBLEM_CONTEXT_TEMPLATE,
    PROBLEM_CONTEXT_FOOTER_TEMPLATE,
    RUNTIME_ERROR_FEEDBACK_TEMPLATE,
    SUCCESS_CLEAN_FEEDBACK_TEMPLATE,
    SUCCESS_NOISY_FEEDBACK_TEMPLATE,
    TIMEOUT_FEEDBACK_TEMPLATE,
    WARNINGS_FOOTER_TEMPLATE,
    FeedbackRenderer,
)

__all__ = [
    "META_FEEDBACK_DIVERSITY_INJECTION",
    "MODE_TEMPLATE_MAP",
    "ModeTemplate",
    "NOISY_PROBLEM_CONTEXT_TEMPLATE",
    "PROBLEM_CONTEXT_FOOTER_TEMPLATE",
    "PromptStrategy",
    "RUNTIME_ERROR_FEEDBACK_TEMPLATE",
    "SUCCESS_CLEAN_FEEDBACK_TEMPLATE",
    "SUCCESS_NOISY_FEEDBACK_TEMPLATE",
    "SynthesisPrompts",
    "TIMEOUT_FEEDBACK_TEMPLATE",
    "WARNINGS_FOOTER_TEMPLATE",
    "assemble_full_prompt",
    "build_example_prompt",
    "build_format_prompt",
    "build_synthesis_prompts",
    "build_task_prompt",
    "FeedbackRenderer",
]
