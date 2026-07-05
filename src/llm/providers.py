"""
LLM Provider Abstraction Layer for LLaMEA.

Uses native LLaMEA LLM classes directly, while resolving environment variables
and patching client settings to support custom endpoint URLs.
"""

import os
from enum import StrEnum
import openai
from llamea import Gemini_LLM, OpenAI_LLM


class Provider(StrEnum):
    GEMINI = "gemini"
    LOCAL = "local"
    LMSTUDIO = "lmstudio"


def build_llm(provider: Provider | str, **kwargs):
    """
    Factory: returns a native LLaMEA LLM instance for the given provider name.
    Automatically retrieves configuration and keys from environment variables.
    """
    match provider:
        case Provider.GEMINI:
            try:
                api_key = os.environ["GOOGLE_API_KEY"]
            except KeyError:
                raise ValueError(
                    "A Gemini API key is required. Set the GOOGLE_API_KEY environment variable."
                )
            model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
            return Gemini_LLM(api_key=api_key, model=model, **kwargs)

        case Provider.LOCAL:
            api_key = os.environ.get("LOCAL_LLM_API_KEY", "not-needed")
            model = os.environ.get("LOCAL_LLM_MODEL", "local-model")
            base_url = os.environ.get("LOCAL_LLM_BASE_URL", "http://localhost:1234/v1")

            # Instantiate native OpenAI_LLM class
            llm = OpenAI_LLM(api_key=api_key, model=model, **kwargs)

            # Patch the client to support custom OpenAI-compatible server URLs (e.g. local llama-server)
            llm.base_url = base_url
            llm._client_kwargs["base_url"] = base_url
            llm.client = openai.OpenAI(**llm._client_kwargs)
            return llm

        case Provider.LMSTUDIO:
            api_key = os.environ.get("LLM_STUDIO_API_KEY", "llm-studio")
            model = os.environ.get("LLM_STUDIO_MODEL", "local-model")
            base_url = os.environ.get("LLM_STUDIO_BASE_URL", "http://localhost:1234/v1")

            # Instantiate native OpenAI_LLM class
            llm = OpenAI_LLM(api_key=api_key, model=model, **kwargs)

            # Patch the client to support custom OpenAI-compatible server URLs (e.g. LM Studio)
            llm.base_url = base_url
            llm._client_kwargs["base_url"] = base_url
            llm.client = openai.OpenAI(**llm._client_kwargs)
            return llm

        case _:
            raise ValueError(f"Unknown provider '{provider}'. Choose from: {list(Provider)}")


__all__ = ["build_llm", "Provider"]
