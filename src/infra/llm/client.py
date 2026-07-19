"""
LLM Provider Abstraction Layer for LLaMEA.

Uses native LLaMEA LLM classes directly, while resolving environment variables
and patching client settings to support custom endpoint URLs.
"""

import os
import urllib.request
from enum import StrEnum
import openai
from llamea import Gemini_LLM, OpenAI_LLM, LLM


class Provider(StrEnum):
    GEMINI = "gemini"
    LOCAL = "local"
    LMSTUDIO = "lmstudio"


class LLMClient:
    """
    Wrapper for LLM clients that provides connection validation,
    telemetry, and safe serialization.
    """

    def __init__(self, provider: Provider | str, skip_validation: bool = False, **kwargs):
        self.provider = provider if isinstance(provider, Provider) else Provider(provider)
        self.skip_validation = skip_validation
        self.kwargs = kwargs
        self._native_client = self._init_native_client()

    @staticmethod
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
                f"  1. Is your model server running? Start it using: bash scripts/llm_server.sh\n"
                f"  2. Check if the port and URL in your .env are correct: {base_url}\n"
                f"  3. Check if any VPN or proxy is blocking localhost connections."
            ) from None

    @staticmethod
    def _get_local_model_name(base_url: str) -> str:
        """Queries the local server's /models endpoint to get the active model name."""
        import json
        import urllib.request
        
        models_url = f"{base_url.rstrip('/')}/models"
        try:
            req = urllib.request.Request(models_url, headers={"User-Agent": "AAD-LLM-Model-Check"})
            with urllib.request.urlopen(req, timeout=1.0) as response:
                data = json.loads(response.read().decode("utf-8"))
                if "data" in data and len(data["data"]) > 0:
                    return data["data"][0].get("id", "local-model")
        except Exception:
            pass
        return "local-model"

    def _init_native_client(self) -> LLM:
        skip_val = self.skip_validation or os.environ.get("SKIP_LLM_VALIDATION") == "True"

        match self.provider:
            case Provider.GEMINI:
                try:
                    api_key = os.environ["GOOGLE_API_KEY"]
                except KeyError:
                    raise ValueError(
                        "A Gemini API key is required. Set the GOOGLE_API_KEY environment variable."
                    )
                model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
                return Gemini_LLM(api_key=api_key, model=model, **self.kwargs)

            case Provider.LOCAL:
                api_key = os.environ.get("LOCAL_LLM_API_KEY", "not-needed")
                base_url = os.environ.get("LOCAL_LLM_BASE_URL", "http://localhost:1234/v1")

                if not skip_val:
                    self._check_connection(base_url, "local")
                    model = self._get_local_model_name(base_url)
                else:
                    model = "local-model"

                llm = OpenAI_LLM(api_key=api_key, model=model, **self.kwargs)
                llm.base_url = base_url
                llm._client_kwargs["base_url"] = base_url
                llm.client = openai.OpenAI(**llm._client_kwargs)
                return llm

            case Provider.LMSTUDIO:
                api_key = os.environ.get("LLM_STUDIO_API_KEY", "llm-studio")
                model = os.environ.get("LLM_STUDIO_MODEL", "local-model")
                base_url = os.environ.get("LLM_STUDIO_BASE_URL", "http://localhost:1234/v1")

                if not skip_val:
                    self._check_connection(base_url, "LM Studio")

                llm = OpenAI_LLM(api_key=api_key, model=model, **self.kwargs)
                llm.base_url = base_url
                llm._client_kwargs["base_url"] = base_url
                llm.client = openai.OpenAI(**llm._client_kwargs)
                return llm

            case _:
                raise ValueError(f"Unknown provider '{self.provider}'. Choose from: {list(Provider)}")

    def sample_solution(
        self,
        session_messages: list,
        parent_ids: list | None = None,
        HPO: bool = False,
        base_code: str | None = None,
        diff_mode: bool = False,
    ):
        import time
        start_t = time.perf_counter()
        sol = self._native_client.sample_solution(
            session_messages=session_messages,
            parent_ids=parent_ids,
            HPO=HPO,
            base_code=base_code,
            diff_mode=diff_mode,
        )
        elapsed = time.perf_counter() - start_t
        if hasattr(sol, "add_metadata"):
            sol.add_metadata("llm_generation_time", elapsed)
        return sol

    @property
    def native_llm(self) -> LLM:
        """The underlying native LLaMEA LLM instance (Gemini_LLM or OpenAI_LLM)."""
        return self._native_client

    @property
    def llm_name(self) -> str:
        """Sanitized name of the LLM model for path creation and database logging."""
        model = getattr(self._native_client, "model", None)
        if not model:
            return "unknown"
        from pathlib import Path
        model_base = Path(model).name
        return model_base.replace(":", "_").replace("/", "_").replace("\\", "_")

    def __getattr__(self, name):
        return getattr(self._native_client, name)

    def __getstate__(self):
        return {
            "provider": self.provider,
            "skip_validation": self.skip_validation,
            "kwargs": self.kwargs,
            "model": getattr(self._native_client, "model", None),
        }

    def __setstate__(self, state):
        self.provider = state["provider"]
        self.skip_validation = state["skip_validation"]
        self.kwargs = state["kwargs"]
        self._native_client = self._init_native_client()
        self._native_client.model = state["model"]


