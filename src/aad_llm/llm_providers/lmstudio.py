"""
LMStudioProvider — LLaMEA connector for LM Studio (and any OpenAI-compatible server).

Supports any server that exposes an OpenAI-compatible /v1 API — including:
  - LM Studio running locally      (http://localhost:1234/v1)
  - Paderborn University server    (set base_url to the remote endpoint)

Usage:
    from aad_llm.llm_providers import build_llm, PROVIDER_LMSTUDIO

    llm = build_llm(
        PROVIDER_LMSTUDIO,
        api_key="llm-studio",
        model="local-model",
        base_url="http://localhost:1234/v1",
    )
"""
import os

import openai
from llamea import OpenAI_LLM


class LMStudioProvider(OpenAI_LLM):
    """
    LLaMEA-compatible connector for LM Studio and OpenAI-compatible local/remote servers.

    Args:
        api_key (str | None): API key sent in the Authorization header.
                              Falls back to LLM_STUDIO_API_KEY env var, then "llm-studio".
        model (str):          Model identifier as configured in LM Studio.
        base_url (str):       Full base URL of the OpenAI-compatible endpoint.
                              Falls back to LLM_STUDIO_BASE_URL env var, then localhost.
    """

    DEFAULT_BASE_URL = "http://localhost:1234/v1"
    DEFAULT_MODEL = "local-model"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        base_url: str | None = None,
        **kwargs,
    ):
        resolved_key = api_key or os.environ.get("LLM_STUDIO_API_KEY", "llm-studio")
        resolved_url = base_url or os.environ.get("LLM_STUDIO_BASE_URL", self.DEFAULT_BASE_URL)

        super().__init__(api_key=resolved_key, model=model, **kwargs)

        # Re-build the underlying openai client with the custom base URL
        self.base_url = resolved_url
        self._client_kwargs["base_url"] = resolved_url
        self.client = openai.OpenAI(**self._client_kwargs)
