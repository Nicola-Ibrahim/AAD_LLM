"""
LLM Provider Abstraction Layer for LLaMEA.

Uses underlying LLaMEA LLM provider classes directly, while resolving environment variables
and patching client settings to support custom endpoint URLs.
"""

from dataclasses import dataclass
from enum import StrEnum
import json
import os
from pathlib import Path
import time
from typing import Any
import urllib.request

import openai
from llamea import LLM, Gemini_LLM, OpenAI_LLM


class Provider(StrEnum):
    GEMINI = "gemini"
    LOCAL = "local"
    LMSTUDIO = "lmstudio"


@dataclass(frozen=True, slots=True)
class EndpointConfig:
    api_key_env: str
    default_api_key: str
    base_url_env: str
    model_env: str
    display_name: str


_OPENAI_ENDPOINTS: dict[Provider, EndpointConfig] = {
    Provider.LOCAL: EndpointConfig(
        api_key_env="LOCAL_LLM_API_KEY",
        default_api_key="not-needed",
        base_url_env="LOCAL_LLM_BASE_URL",
        model_env="LOCAL_LLM_MODEL",
        display_name="local",
    ),
    Provider.LMSTUDIO: EndpointConfig(
        api_key_env="LLM_STUDIO_API_KEY",
        default_api_key="llm-studio",
        base_url_env="LLM_STUDIO_BASE_URL",
        model_env="LLM_STUDIO_MODEL",
        display_name="LM Studio",
    ),
}


class ModelInfo(str):
    """String representation of an LLM model with a .name property for sanitized access."""

    @property
    def name(self) -> str:
        """Sanitized model name for directory paths and database logging."""
        return Path(self).name.replace(":", "_").replace("/", "_").replace("\\", "_")


class LLMClient:
    """
    Wrapper for LLM client connections providing connection validation,
    telemetry, and safe serialization.
    """

    def __init__(
        self,
        provider: Provider | str,
        validate_on_init: bool = True,
        **kwargs: Any,
    ):
        self.provider = provider if isinstance(provider, Provider) else Provider(provider)
        self.validate_on_init = validate_on_init
        self.kwargs = kwargs
        self._client = self._init_client()

    def validate_connection(self) -> None:
        """Explicitly probe and validate network reachability to the LLM backend."""
        if config := _OPENAI_ENDPOINTS.get(self.provider):
            base_url = os.environ.get(config.base_url_env, "http://localhost:1234/v1")
            self._check_connection(base_url, config.display_name)

    @staticmethod
    def _check_connection(base_url: str, provider_name: str) -> None:
        """Checks if the local LLM server is reachable at the given base URL."""
        models_url = f"{base_url.rstrip('/')}/models"
        try:
            req = urllib.request.Request(
                models_url, headers={"User-Agent": "AAD-LLM-Connection-Check"}
            )
            with urllib.request.urlopen(req, timeout=10.0):
                pass
        except Exception as e:
            raise ConnectionError(
                f"Could not connect to the {provider_name} LLM server at '{base_url}'.\n"
                f"Error details: {e}\n"
                f"Troubleshooting:\n"
                f"  1. Is your model server running? Start it using: bash scripts/llm.sh\n"
                f"  2. Check if the port and URL in your .env are correct: {base_url}\n"
                f"  3. Check if any VPN or proxy is blocking localhost connections."
            ) from None

    @staticmethod
    def _get_local_model_name(base_url: str) -> str:
        """Queries the local server's /models endpoint to get the active model name."""
        models_url = f"{base_url.rstrip('/')}/models"
        try:
            req = urllib.request.Request(models_url, headers={"User-Agent": "AAD-LLM-Model-Check"})
            with urllib.request.urlopen(req, timeout=5.0) as response:
                data = json.loads(response.read().decode("utf-8"))
                if (models := data.get("data")) and (model_id := models[0].get("id")):
                    return model_id
        except Exception as e:
            raise ConnectionError(
                f"Could not fetch active model from local server at '{models_url}'.\n"
                f"Error details: {e}\n"
                f"Ensure your model server is running (e.g. bash scripts/llm.sh start) "
                f"or specify the model explicitly via LOCAL_LLM_MODEL or model='...'."
            ) from None

        raise RuntimeError(
            f"No models found on the local LLM server at '{models_url}'. "
            f"Ensure a model is actively loaded on the server."
        )

    def _init_client(self) -> LLM:
        should_validate = self.validate_on_init and os.environ.get("SKIP_LLM_VALIDATION") != "True"

        if self.provider == Provider.GEMINI:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError(
                    "A Gemini API key is required. Set the GOOGLE_API_KEY environment variable."
                )
            model = self.kwargs.pop("model", None) or os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
            return Gemini_LLM(api_key=api_key, model=model, **self.kwargs)

        if config := _OPENAI_ENDPOINTS.get(self.provider):
            return self._init_openai_compatible(config, should_validate)

        raise ValueError(f"Unknown provider '{self.provider}'. Choose from: {list(Provider)}")

    def _init_openai_compatible(self, config: EndpointConfig, should_validate: bool) -> OpenAI_LLM:
        base_url = os.environ.get(config.base_url_env, "http://localhost:1234/v1")
        api_key = os.environ.get(config.api_key_env, config.default_api_key)
        model = self.kwargs.pop("model", None) or os.environ.get(config.model_env)

        if should_validate:
            self._check_connection(base_url, config.display_name)
            model = model or self._get_local_model_name(base_url)
        elif not model:
            raise ValueError(
                f"No model specified for {config.display_name} LLM provider. "
                f"Either run the local LLM server so the model can be auto-detected, "
                f"or configure {config.model_env}."
            )

        llm = OpenAI_LLM(api_key=api_key, model=model, **self.kwargs)
        llm.base_url = base_url
        llm._client_kwargs["base_url"] = base_url
        llm.client = openai.OpenAI(**llm._client_kwargs)
        return llm

    def sample_solution(
        self,
        session_messages: list,
        parent_ids: list | None = None,
        HPO: bool = False,
        base_code: str | None = None,
        diff_mode: bool = False,
    ):
        """Samples a solution from the LLM with retry and telemetry tracking."""
        max_retries = 3
        backoff = 2.0

        for attempt in range(1, max_retries + 1):
            try:
                start_t = time.perf_counter()
                sol = self._client.sample_solution(
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
            except Exception:
                if attempt == max_retries:
                    raise
                time.sleep(backoff * attempt)

    @property
    def model(self) -> ModelInfo:
        """Model identifier string wrapped as ModelInfo to allow accessing .name directly."""
        raw_model = getattr(self._client, "model", "unknown") or "unknown"
        return ModelInfo(raw_model)

    def __getattr__(self, name: str) -> Any:
        if "_client" not in self.__dict__:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return getattr(self._client, name)

    def __getstate__(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "validate_on_init": getattr(self, "validate_on_init", False),
            "kwargs": self.kwargs,
            "model": getattr(self._client, "model", None),
        }

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.provider = state["provider"]
        self.validate_on_init = False
        self.kwargs = state["kwargs"].copy()
        if state.get("model"):
            self.kwargs.setdefault("model", state["model"])
        self._client = self._init_client()
        if state.get("model"):
            self._client.model = state["model"]
