"""Read the configured model registry and construct pure naming rules."""

from functools import lru_cache
from pathlib import Path
import re
import tomllib
from typing import Optional

from benchmarking.domain.services.resolvers import LLMModelSpec, ModelNames


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


def configured_model_names(toml_path: Path | None = None) -> ModelNames:
    return ModelNames(load_llm_registry(toml_path))
