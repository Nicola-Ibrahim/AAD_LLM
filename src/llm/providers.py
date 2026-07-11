"""
LLM Provider Abstraction Layer for LLaMEA.

Uses native LLaMEA LLM classes directly, while resolving environment variables
and patching client settings to support custom endpoint URLs.
"""

import os
import urllib.request
from enum import StrEnum
import openai
from llamea import Gemini_LLM, OpenAI_LLM


class Provider(StrEnum):
    GEMINI = "gemini"
    LOCAL = "local"
    LMSTUDIO = "lmstudio"


def _check_connection(base_url: str, provider_name: str) -> None:
    """Checks if the local LLM server is reachable at the given base URL."""
    models_url = f"{base_url.rstrip('/')}/models"
    try:
        req = urllib.request.Request(models_url, headers={"User-Agent": "AAD-LLM-Connection-Check"})
        with urllib.request.urlopen(req, timeout=2.0) as _:
            pass
    except Exception as e:
        raise ConnectionError(
            f"Could not connect to the {provider_name} LLM server at '{base_url}'.\n"
            f"Error details: {e}\n"
            f"Troubleshooting:\n"
            f"  1. Is your model server running? Start it using: bash scripts/03_serve_llm.sh\n"
            f"  2. Check if the port and URL in your .env are correct: {base_url}\n"
            f"  3. Check if any VPN or proxy is blocking localhost connections."
        ) from None


def _wrap_sample_solution(llm):
    """Wraps sample_solution to measure prompt generation execution time."""
    original_sample_solution = llm.sample_solution

    def patched_sample_solution(*args, **kwargs):
        import time

        start_t = time.perf_counter()
        sol = original_sample_solution(*args, **kwargs)
        elapsed = time.perf_counter() - start_t
        sol.add_metadata("llm_generation_time", elapsed)
        return sol

    llm.sample_solution = patched_sample_solution
    return llm


def get_llm_client(provider: Provider | str, skip_validation: bool = False, **kwargs):
    """
    Factory: returns a native LLaMEA LLM instance for the given provider name.
    Automatically retrieves configuration and keys from environment variables.
    """
    skip_val = skip_validation or os.environ.get("SKIP_LLM_VALIDATION") == "True"

    match provider:
        case Provider.GEMINI:
            try:
                api_key = os.environ["GOOGLE_API_KEY"]
            except KeyError:
                raise ValueError(
                    "A Gemini API key is required. Set the GOOGLE_API_KEY environment variable."
                )
            model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
            client = Gemini_LLM(api_key=api_key, model=model, **kwargs)
            return _wrap_sample_solution(client)

        case Provider.LOCAL:
            api_key = os.environ.get("LOCAL_LLM_API_KEY", "not-needed")
            model = os.environ.get("LOCAL_LLM_MODEL", "local-model")
            base_url = os.environ.get("LOCAL_LLM_BASE_URL", "http://localhost:1234/v1")

            if not skip_val:
                _check_connection(base_url, "local")

            # Instantiate native OpenAI_LLM class
            llm = OpenAI_LLM(api_key=api_key, model=model, **kwargs)

            # Patch the client to support custom OpenAI-compatible server URLs (e.g. local llama-server)
            llm.base_url = base_url
            llm._client_kwargs["base_url"] = base_url
            llm.client = openai.OpenAI(**llm._client_kwargs)
            return _wrap_sample_solution(llm)

        case Provider.LMSTUDIO:
            api_key = os.environ.get("LLM_STUDIO_API_KEY", "llm-studio")
            model = os.environ.get("LLM_STUDIO_MODEL", "local-model")
            base_url = os.environ.get("LLM_STUDIO_BASE_URL", "http://localhost:1234/v1")

            if not skip_val:
                _check_connection(base_url, "LM Studio")

            # Instantiate native OpenAI_LLM class
            llm = OpenAI_LLM(api_key=api_key, model=model, **kwargs)

            # Patch the client to support custom OpenAI-compatible server URLs (e.g. LM Studio)
            llm.base_url = base_url
            llm._client_kwargs["base_url"] = base_url
            llm.client = openai.OpenAI(**llm._client_kwargs)
            return _wrap_sample_solution(llm)

        case _:
            raise ValueError(f"Unknown provider '{provider}'. Choose from: {list(Provider)}")


__all__ = ["get_llm_client", "Provider"]
