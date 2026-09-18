"""LLaMEA Engine Adapter Package.

Contains the concrete adapter implementation for algorithm synthesis using LLaMEA.
"""

from evolution.infra.engines.llamea.evaluator import Evaluator
from evolution.infra.engines.llamea.prompts import (
    SynthesisPrompts,
    assemble_full_prompt,
    build_synthesis_prompts,
    build_task_prompt,
)
from evolution.infra.engines.llamea.runner import LLaMEAEngine, LLaMEASession

__all__ = [
    "Evaluator",
    "LLaMEAEngine",
    "LLaMEASession",
    "SynthesisPrompts",
    "assemble_full_prompt",
    "build_synthesis_prompts",
    "build_task_prompt",
]
