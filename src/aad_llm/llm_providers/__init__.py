"""
LLM Provider Abstraction Layer for LLaMEA.

Exports:
  - build_llm(provider, **kwargs)
  - PROVIDER_GEMINI = "gemini"
  - PROVIDER_LMSTUDIO = "lmstudio"
"""

from aad_llm.llm_providers.gemini import GeminiProvider
from aad_llm.llm_providers.lmstudio import LMStudioProvider

PROVIDER_GEMINI = "gemini"
PROVIDER_LMSTUDIO = "lmstudio"

def build_llm(provider: str, **kwargs):
    """
    Factory: returns a LLaMEA-compatible LLM instance for the given provider name.
    kwargs are forwarded directly to the provider's constructor.
    """
    registry = {
        PROVIDER_GEMINI: GeminiProvider,
        PROVIDER_LMSTUDIO: LMStudioProvider,
    }
    if provider not in registry:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Choose from: {list(registry.keys())}"
        )
    return registry[provider](**kwargs)

__all__ = ["build_llm", "PROVIDER_GEMINI", "PROVIDER_LMSTUDIO"]
