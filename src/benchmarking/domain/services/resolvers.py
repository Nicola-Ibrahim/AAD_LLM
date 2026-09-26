"""Pure solver and model naming rules over an injected model registry."""

from dataclasses import dataclass
import re
from collections.abc import Sequence

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


class ModelNames:
    """Format model and solver names without reading configuration files."""

    def __init__(self, registry: Sequence[LLMModelSpec]) -> None:
        self.registry = tuple(registry)

    def get_registered_model_ids(self) -> list[str]:
        """Retrieve all model identifiers and filenames defined in configs/llms.toml."""
        registry = self.registry
        ids: list[str] = []
        for spec in registry:
            if spec.model and spec.model not in ids:
                ids.append(spec.model)
            if spec.file and spec.file not in ids:
                ids.append(spec.file)
        return ids

    def get_clean_model_label(self, llm_name: str) -> str:
        """Return the full configured model name, with dynamic fallback for unknown IDs.

        Registered IDs resolve to their complete ``name`` (including suffixes such as
        ``-Instruct``), rather than the abbreviated display tag.
        """
        if not llm_name:
            return "LLM"

        s = llm_name.strip()
        s_lower = s.lower().removesuffix(".gguf")
        normalized_s = re.sub(r"[^a-z0-9]", "", s_lower)
        specs = self.registry

        # 1. Exact or direct normalized match in registry
        for spec in specs:
            identifiers = (spec.model, spec.file, spec.name, spec.tag)
            normalized_identifiers = {
                re.sub(r"[^a-z0-9]", "", identifier.lower().removesuffix(".gguf"))
                for identifier in identifiers
                if identifier
            }
            if normalized_s in normalized_identifiers:
                return spec.name

        # 2. Substring containment match for model ID or filename
        for spec in specs:
            normalized_identifiers = (
                re.sub(r"[^a-z0-9]", "", identifier.lower().removesuffix(".gguf"))
                for identifier in (spec.model, spec.file)
            )
            if any(identifier and identifier in normalized_s for identifier in normalized_identifiers):
                return spec.name

        # 3. Family + Parameter Size matching (e.g. "qwen_14b" -> matches Qwen family with 14B size)
        size_m = re.search(r"(\d+(?:\.\d+)?b)", s_lower)
        size_str = size_m.group(1) if size_m else ""

        if size_str:
            for spec in specs:
                if spec.size_slug == size_str:
                    if spec.family_slug in s_lower or spec.category.lower() in s_lower:
                        return spec.name

        # 4. Fallback if family is registered in llms.toml categories
        for spec in specs:
            if spec.family_slug in s_lower or spec.category.lower() in s_lower:
                if size_str:
                    return re.sub(
                        re.escape(spec.size_slug),
                        size_str.upper(),
                        spec.name,
                        count=1,
                        flags=re.IGNORECASE,
                    )
                return spec.name

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

    def format_db_solver_name(self, llm_name: str, prompt_strategy: str) -> str:
        """Format combined solver name from DB record e.g., 'Qwen2.5-Coder-14B / baseline'."""
        model_lbl = self.get_clean_model_label(llm_name)
        strat = prompt_strategy.lower() if prompt_strategy else "baseline"
        return f"{model_lbl} / {strat}"

    def get_model_slug(self, llm_name: str) -> str:
        """Generate filesystem-safe model slug (e.g. 'qwen_14b', 'llama_8b', 'deepseek_70b')."""
        if not llm_name:
            return "llamea"

        name_lower = llm_name.lower()
        specs = self.registry

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

        return name_lower.removesuffix(".gguf").replace("-", "_").replace(".", "_").split("/")[-1]

    def resolve_folder_solver_name(self, folder_name: str) -> str:
        """Map any evaluation directory folder name to canonical display name using llms.toml tags."""
        raw = folder_name.strip()
        p = re.sub(r"(-\d+|\.\d+)$", "", raw.lower())

        # 1. Classical Baselines
        if p in CLASSICAL_SOLVERS_MAP:
            return CLASSICAL_SOLVERS_MAP[p]
        if p == "de" or p.startswith(("de_", "de-")) or "_de_" in p:
            return ClassicalSolver.DE
        if "cma" in p:
            return ClassicalSolver.CMA_ES
        if "pso" in p:
            return ClassicalSolver.PSO

        # 2. Structured LLM Folders: {model_slug}_{strategy} (with optional noise adaptation flag)
        is_noise_adapted = ("_noisy" in p) or ("noisy_" in p) or ("-noisy" in p)
        is_noise_implicit = ("_implicit" in p) or ("implicit_" in p) or ("-implicit" in p)
        clean_p = (
            p.replace("_noisy", "")
            .replace("noisy_", "")
            .replace("-noisy", "")
            .replace("_implicit", "")
            .replace("implicit_", "")
            .replace("-implicit", "")
        )
        if is_noise_adapted:
            suffix = " (noise-adapted)"
        elif is_noise_implicit:
            suffix = " (noise-implicit)"
        else:
            suffix = ""

        for s in KNOWN_STRATEGIES:
            if clean_p.endswith(f"_{s}") or clean_p.endswith(f"-{s}"):
                model_part = clean_p[: -(len(s) + 1)]
                model_lbl = self.get_clean_model_label(model_part)
                return f"{model_lbl} / {s}{suffix}"

        # 3. Legacy aliases fallback
        for s in KNOWN_STRATEGIES:
            if s in clean_p:
                model_lbl = self.get_clean_model_label(clean_p)
                return f"{model_lbl} / {s}{suffix}"

        return raw

    def resolve_canonical_model_slug(
        self, model_slug: str, known_models: list[str] | None = None
    ) -> str:
        """Normalize model slug for figure output directories using registered model IDs."""
        slug_str = model_slug.lower()
        models_to_check = known_models or self.get_registered_model_ids()
        for db_m in models_to_check:
            clean_db = db_m.removesuffix(".gguf")
            if clean_db.lower() == slug_str or db_m.lower() == slug_str:
                return clean_db
            m = re.search(r"(\d+b)", slug_str)
            if m and m.group(1) in clean_db.lower():
                return clean_db

        return model_slug.replace("LLaMEA-", "").replace(" ", "_").removesuffix(".gguf")
