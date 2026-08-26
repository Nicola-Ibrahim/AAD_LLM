"""Dynamic Solver and Model Name Normalization.

Provides robust rule-based resolvers with zero hardcoded model dictionaries,
ensuring automatic support for any current or future model size (7B, 14B, 32B, 70B, etc.)
and classical baseline algorithm.
"""

import re
from typing import Final

# Recognized classical optimization baselines
CLASSICAL_SOLVERS_MAP: Final[dict[str, str]] = {
    "cmaes": "CMA-ES",
    "cma_es": "CMA-ES",
    "cma-es": "CMA-ES",
    "de": "DE",
    "pso": "PSO",
}

KNOWN_STRATEGIES: Final[list[str]] = [
    "baseline",
    "guided",
    "thinking",
    "vectorization",
    "champion",
]


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
        return CLASSICAL_SOLVERS_MAP[p]
    if p == "de" or p.startswith(("de_", "de-")) or "_de_" in p:
        return "DE"
    if "cma" in p:
        return "CMA-ES"
    if "pso" in p:
        return "PSO"

    # 2. Structured LLM Folders: {model_slug}_{strategy}
    for s in KNOWN_STRATEGIES:
        if p.endswith(f"_{s}") or p.endswith(f"-{s}"):
            model_part = p[: -(len(s) + 1)]
            size_m = re.search(r"(\d+b)", model_part)
            if size_m:
                return f"LLaMEA-{size_m.group(1).upper()} / {s}"
            clean_m = (
                model_part.replace("llamea", "")
                .strip("_-")
                .replace("_", " ")
                .title()
            )
            return f"LLaMEA-{clean_m} / {s}" if clean_m else f"LLaMEA / {s}"

    # 3. Legacy aliases
    if "thinking" in p:
        return "LLaMEA / thinking"
    if "vectorization" in p:
        return "LLaMEA / vectorization"
    if "guided" in p:
        return "LLaMEA / guided"
    if "baseline" in p:
        return "LLaMEA / baseline"

    return raw


def resolve_canonical_model_slug(model_slug: str, known_models: list[str] | None = None) -> str:
    """Normalize model slug for figure output directories."""
    slug_str = str(model_slug).lower()
    if known_models:
        for db_m in known_models:
            clean_db = db_m.removesuffix(".gguf")
            if clean_db.lower() == slug_str or db_m.lower() == slug_str:
                return clean_db
            m = re.search(r"(\d+b)", slug_str)
            if m and m.group(1) in clean_db.lower():
                return clean_db

    return str(model_slug).replace("LLaMEA-", "").replace(" ", "_").removesuffix(".gguf")
