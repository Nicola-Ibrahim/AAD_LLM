"""Dynamic Solver and Model Name Normalization.

Provides robust rule-based resolvers with zero hardcoded model dictionaries,
ensuring automatic support for any current or future model size (7B, 14B, 32B, 70B, etc.)
and classical baseline algorithm.
"""

import re
from typing import Final

from benchmarking.domain.enums.benchmark_strategy import BenchmarkStrategy
from benchmarking.domain.enums.classical_solver import ClassicalSolver

# Recognized classical optimization baselines
CLASSICAL_SOLVERS_MAP: Final[dict[str, ClassicalSolver]] = {
    "cmaes": ClassicalSolver.CMA_ES,
    "cma_es": ClassicalSolver.CMA_ES,
    "cma-es": ClassicalSolver.CMA_ES,
    "de": ClassicalSolver.DE,
    "pso": ClassicalSolver.PSO,
}

KNOWN_STRATEGIES: Final[list[BenchmarkStrategy]] = list(BenchmarkStrategy)


def get_clean_model_label(llm_name: str) -> str:
    """Derive clean publication-ready model label e.g., 'LLaMEA-14B', 'LLaMEA-70B'."""
    if not llm_name:
        return "LLaMEA"

    name_lower = str(llm_name).lower()
    m = re.search(r"(\d+b)", name_lower)
    if m:
        return f"LLaMEA-{m.group(1).upper()}"

    clean = (
        name_lower.removesuffix(".gguf")
        .replace("-instruct", "")
        .replace("-chat", "")
        .replace("-", " ")
        .replace("_", " ")
        .split("/")[-1]
        .strip()
    )
    return f"LLaMEA-{clean.title()}" if clean else "LLaMEA"


def format_db_solver_name(llm_name: str, prompt_strategy: str) -> str:
    """Format combined solver name from DB record e.g., 'LLaMEA-14B / baseline'."""
    model_lbl = get_clean_model_label(llm_name)
    strat = str(prompt_strategy).lower() if prompt_strategy else "baseline"
    return f"{model_lbl} / {strat}"


def get_model_slug(llm_name: str) -> str:
    """Generate filesystem-safe model slug (e.g. 'qwen_14b', 'llama_8b', 'qwen_70b')."""
    if not llm_name:
        return "llamea"

    name_lower = str(llm_name).lower()
    family_m = re.search(r"([a-zA-Z]+)[^a-zA-Z0-9]*.*?(\d+b)", name_lower)
    if family_m:
        return f"{family_m.group(1)}_{family_m.group(2)}"

    size_m = re.search(r"(\d+b)", name_lower)
    if size_m:
        return f"qwen_{size_m.group(1)}"

    return (
        name_lower.removesuffix(".gguf")
        .replace("-", "_")
        .replace(".", "_")
        .split("/")[-1]
    )


def resolve_folder_solver_name(folder_name: str) -> str:
    """Map any evaluation directory folder name to canonical display name."""
    raw = folder_name.strip()
    p = re.sub(r"(-\d+|\.\d+)$", "", raw.lower())

    # 1. Classical Baselines
    if p in CLASSICAL_SOLVERS_MAP:
        return str(CLASSICAL_SOLVERS_MAP[p].value)
    if p == "de" or p.startswith(("de_", "de-")) or "_de_" in p:
        return ClassicalSolver.DE.value
    if "cma" in p:
        return ClassicalSolver.CMA_ES.value
    if "pso" in p:
        return ClassicalSolver.PSO.value

    # 2. Structured LLM Folders: {model_slug}_{strategy}
    for s in KNOWN_STRATEGIES:
        strat_val = s.value if isinstance(s, BenchmarkStrategy) else str(s)
        if p.endswith(f"_{strat_val}") or p.endswith(f"-{strat_val}"):
            model_part = p[: -(len(strat_val) + 1)]
            size_m = re.search(r"(\d+b)", model_part)
            if size_m:
                return f"LLaMEA-{size_m.group(1).upper()} / {strat_val}"
            clean_m = (
                model_part.replace("llamea", "")
                .strip("_-")
                .replace("_", " ")
                .title()
            )
            return f"LLaMEA-{clean_m} / {strat_val}" if clean_m else f"LLaMEA / {strat_val}"

    # 3. Legacy aliases
    if BenchmarkStrategy.THINKING.value in p:
        return f"LLaMEA / {BenchmarkStrategy.THINKING.value}"
    if BenchmarkStrategy.VECTORIZATION.value in p:
        return f"LLaMEA / {BenchmarkStrategy.VECTORIZATION.value}"
    if BenchmarkStrategy.GUIDED.value in p:
        return f"LLaMEA / {BenchmarkStrategy.GUIDED.value}"
    if BenchmarkStrategy.BASELINE.value in p:
        return f"LLaMEA / {BenchmarkStrategy.BASELINE.value}"

    return raw


DEFAULT_KNOWN_MODELS: Final[list[str]] = [
    "qwen2.5-coder-14b-instruct-q4_k_m",
    "qwen2.5-coder-7b-instruct-q4_k_m",
]


def resolve_canonical_model_slug(model_slug: str, known_models: list[str] | None = None) -> str:
    """Normalize model slug for figure output directories."""
    slug_str = str(model_slug).lower()
    models_to_check = known_models or DEFAULT_KNOWN_MODELS
    for db_m in models_to_check:
        clean_db = db_m.removesuffix(".gguf")
        if clean_db.lower() == slug_str or db_m.lower() == slug_str:
            return clean_db
        m = re.search(r"(\d+b)", slug_str)
        if m and m.group(1) in clean_db.lower():
            return clean_db

    return str(model_slug).replace("LLaMEA-", "").replace(" ", "_").removesuffix(".gguf")
