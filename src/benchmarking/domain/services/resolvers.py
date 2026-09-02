"""Dynamic Solver and Model Name Normalization.

Provides configuration-driven resolvers powered by configs/llms.toml,
ensuring zero hardcoding of model dictionaries while supporting any present
or future model architecture, size, quantization, or baseline algorithm.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re
import tomllib
from typing import Optional

from benchmarking.domain.enums.benchmark_strategy import EvaluationStrategy
from benchmarking.domain.enums.classical_solver import ClassicalSolver

# Recognized classical optimization baselines
CLASSICAL_SOLVERS_MAP: dict[str, ClassicalSolver] = {
    "cmaes": ClassicalSolver.CMA_ES,
    "cma_es": ClassicalSolver.CMA_ES,
    "cma-es": ClassicalSolver.CMA_ES,
    "de": ClassicalSolver.DE,
    "pso": ClassicalSolver.PSO,
}

KNOWN_STRATEGIES: list[EvaluationStrategy] = list(EvaluationStrategy)


@dataclass(frozen=True)
class LLMModelSpec:
    """Registry entry representing an LLM model configured in llms.toml."""

    category: str
    name: str
    tag: str
    file: str
    model: str
    family_slug: str
    size_slug: str


@lru_cache(maxsize=1)
def load_llm_registry(toml_path: Optional[Path] = None) -> list[LLMModelSpec]:
    """Load LLM specifications and clean display tags from configs/llms.toml."""
    if toml_path is None:
        candidates = [
            Path("configs/llms.toml"),
            Path(__file__).resolve().parents[5] / "configs" / "llms.toml"
            if len(Path(__file__).resolve().parents) >= 6
            else None,
        ]
        # Also try locating by walking parent directories
        curr = Path(__file__).resolve().parent
        for _ in range(8):
            cand = curr / "configs" / "llms.toml"
            if cand.is_file():
                candidates.insert(0, cand)
                break
            if curr.parent == curr:
                break
            curr = curr.parent

        for c in candidates:
            if c and c.is_file():
                toml_path = c
                break

    if not toml_path or not toml_path.is_file():
        return []

    try:
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
    except Exception:
        return []

    registry: list[LLMModelSpec] = []
    for cat_name, cat_data in data.items():
        if not isinstance(cat_data, dict):
            continue
        family = str(cat_name).lower()
        for item in cat_data.get("llms", []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            tag = str(item.get("tag") or name).strip()
            file_name = str(item.get("file", "")).strip()
            model_id = str(item.get("model", "")).strip()

            combined_str = f"{name} {tag} {file_name} {model_id}".lower()
            size_m = re.search(r"(\d+(?:\.\d+)?b)", combined_str)
            size_slug = size_m.group(1) if size_m else ""

            registry.append(
                LLMModelSpec(
                    category=cat_name,
                    name=name,
                    tag=tag,
                    file=file_name,
                    model=model_id,
                    family_slug=family,
                    size_slug=size_slug,
                )
            )
    return registry


def get_registered_model_ids() -> list[str]:
    """Retrieve all model identifiers and filenames defined in configs/llms.toml."""
    registry = load_llm_registry()
    ids: list[str] = []
    for spec in registry:
        if spec.model and spec.model not in ids:
            ids.append(spec.model)
        if spec.file and spec.file not in ids:
            ids.append(spec.file)
    return ids


def get_clean_model_label(llm_name: str) -> str:
    """Derive clean publication-ready LLM model label dynamically from configs/llms.toml tags.

    Matches against configured tags (e.g. 'Qwen2.5-Coder-7B', 'Qwen2.5-Coder-14B', 'Llama-8B')
    without any hardcoded model conditional branches.
    """
    if not llm_name:
        return "LLM"

    s = llm_name.strip()
    s_lower = s.lower().removesuffix(".gguf")
    specs = load_llm_registry()

    # 1. Exact or direct normalized match in registry
    for spec in specs:
        spec_model = spec.model.lower().removesuffix(".gguf")
        spec_file = spec.file.lower().removesuffix(".gguf")
        spec_name = spec.name.lower().removesuffix(".gguf")
        spec_tag = spec.tag.lower()
        if s_lower in (spec_model, spec_file, spec_name, spec_tag):
            return spec.tag

    # 2. Substring containment match for model ID or filename
    for spec in specs:
        spec_model = spec.model.lower().removesuffix(".gguf")
        spec_file = spec.file.lower().removesuffix(".gguf")
        if (spec_model and spec_model in s_lower) or (spec_file and spec_file in s_lower):
            return spec.tag

    # 3. Family + Parameter Size matching (e.g. "qwen_14b" -> matches Qwen family with 14B size)
    size_m = re.search(r"(\d+(?:\.\d+)?b)", s_lower)
    size_str = size_m.group(1) if size_m else ""

    if size_str:
        for spec in specs:
            if spec.size_slug == size_str:
                if spec.family_slug in s_lower or spec.category.lower() in s_lower:
                    return spec.tag

    # 4. Fallback if family is registered in llms.toml categories
    for spec in specs:
        if spec.family_slug in s_lower or spec.category.lower() in s_lower:
            if size_str:
                prefix = spec.tag.rsplit("-", 1)[0] if "-" in spec.tag else spec.category
                return f"{prefix}-{size_str.upper()}"
            return spec.tag

    # 5. Generic dynamic fallback for unregistered models (e.g. "mistral-7b" -> "Mistral-7B")
    if size_str:
        m = re.search(r"([a-zA-Z]+)", s_lower)
        fam = m.group(1).title() if m else "LLM"
        return f"{fam}-{size_str.upper()}"

    clean = (
        s_lower.replace("-instruct", "")
        .replace("-chat", "")
        .replace("-", " ")
        .replace("_", " ")
        .split("/")[-1]
        .strip()
    )
    return clean.title() if clean else "LLM"


def format_db_solver_name(llm_name: str, prompt_strategy: str) -> str:
    """Format combined solver name from DB record e.g., 'Qwen2.5-Coder-14B / baseline'."""
    model_lbl = get_clean_model_label(llm_name)
    strat = prompt_strategy.lower() if prompt_strategy else "baseline"
    return f"{model_lbl} / {strat}"


def get_model_slug(llm_name: str) -> str:
    """Generate filesystem-safe model slug (e.g. 'qwen_14b', 'llama_8b', 'deepseek_70b')."""
    if not llm_name:
        return "llamea"

    name_lower = llm_name.lower()
    specs = load_llm_registry()

    # Check registry match first
    for spec in specs:
        spec_model = spec.model.lower().removesuffix(".gguf")
        spec_file = spec.file.lower().removesuffix(".gguf")
        if name_lower in (spec_model, spec_file) or (spec_model and spec_model in name_lower):
            if spec.size_slug:
                return f"{spec.family_slug}_{spec.size_slug}"

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
    """Map any evaluation directory folder name to canonical display name using llms.toml tags."""
    raw = folder_name.strip()
    p = re.sub(r"(-\d+|\.\d+)$", "", raw.lower())

    # 1. Classical Baselines
    if p in CLASSICAL_SOLVERS_MAP:
        return CLASSICAL_SOLVERS_MAP[p].value
    if p == "de" or p.startswith(("de_", "de-")) or "_de_" in p:
        return ClassicalSolver.DE.value
    if "cma" in p:
        return ClassicalSolver.CMA_ES.value
    if "pso" in p:
        return ClassicalSolver.PSO.value

    # 2. Structured LLM Folders: {model_slug}_{strategy} (with optional noise adaptation flag)
    is_noise_adapted = ("_noisy" in p) or ("noisy_" in p) or ("-noisy" in p)
    clean_p = p.replace("_noisy", "").replace("noisy_", "").replace("-noisy", "")
    suffix = " (noise-adapted)" if is_noise_adapted else ""

    for s in KNOWN_STRATEGIES:
        strat_val = s.value if isinstance(s, EvaluationStrategy) else str(s)
        if clean_p.endswith(f"_{strat_val}") or clean_p.endswith(f"-{strat_val}"):
            model_part = clean_p[: -(len(strat_val) + 1)]
            model_lbl = get_clean_model_label(model_part)
            return f"{model_lbl} / {strat_val}{suffix}"

    # 3. Legacy aliases fallback
    for s in KNOWN_STRATEGIES:
        strat_val = s.value if isinstance(s, EvaluationStrategy) else str(s)
        if strat_val in clean_p:
            model_lbl = get_clean_model_label(clean_p)
            return f"{model_lbl} / {strat_val}{suffix}"

    return raw


def resolve_canonical_model_slug(model_slug: str, known_models: list[str] | None = None) -> str:
    """Normalize model slug for figure output directories using registered model IDs."""
    slug_str = model_slug.lower()
    models_to_check = known_models or get_registered_model_ids()
    for db_m in models_to_check:
        clean_db = db_m.removesuffix(".gguf")
        if clean_db.lower() == slug_str or db_m.lower() == slug_str:
            return clean_db
        m = re.search(r"(\d+b)", slug_str)
        if m and m.group(1) in clean_db.lower():
            return clean_db

    return model_slug.replace("LLaMEA-", "").replace(" ", "_").removesuffix(".gguf")
