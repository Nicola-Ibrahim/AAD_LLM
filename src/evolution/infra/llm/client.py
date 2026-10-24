"""
LLM Provider Abstraction Layer for LLaMEA.

Uses underlying LLaMEA LLM provider classes directly, while resolving environment variables
and patching client settings to support custom endpoint URLs.
"""

import json
import os
import time
import urllib.request
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import openai
from llamea import LLM, Gemini_LLM, OpenAI_LLM
from llamea.solution import Solution

from evolution.infra.llm.gateway import GatewayLLM, GatewayRequestLimiter


class Provider(StrEnum):
    GEMINI = "gemini"
    LOCAL = "local"
    LMSTUDIO = "lmstudio"
    UPB = "upb"


@dataclass(frozen=True, slots=True)
class EndpointConfig:
    api_key_env: str
    default_api_key: str
    base_url_env: str
    model_env: str
    display_name: str
    default_base_url: str


_OPENAI_ENDPOINTS: dict[Provider, EndpointConfig] = {
    Provider.LOCAL: EndpointConfig(
        api_key_env="LOCAL_LLM_API_KEY",
        default_api_key="not-needed",
        base_url_env="LOCAL_LLM_BASE_URL",
        model_env="LOCAL_LLM_MODEL",
        display_name="local",
        default_base_url="http://localhost:1234/v1",
    ),
    Provider.LMSTUDIO: EndpointConfig(
        api_key_env="LLM_STUDIO_API_KEY",
        default_api_key="llm-studio",
        base_url_env="LLM_STUDIO_BASE_URL",
        model_env="LLM_STUDIO_MODEL",
        display_name="LM Studio",
        default_base_url="http://localhost:1234/v1",
    ),
    Provider.UPB: EndpointConfig(
        api_key_env="UPB_API_KEY",
        default_api_key="",
        base_url_env="UPB_API_BASE",
        model_env="UPB_MODEL",
        display_name="University Paderborn AI Gateway",
        default_base_url="https://ai-gateway.uni-paderborn.de/v1/",
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
    ) -> None:
        self.provider = provider if isinstance(provider, Provider) else Provider(provider)
        self.validate_on_init = validate_on_init
        self.kwargs = kwargs
        self._client = self._init_client()

    def validate_connection(self) -> None:
        """Explicitly probe and validate network reachability to the LLM backend."""
        if self.provider == Provider.UPB:
            self.list_models()
            return
        if config := _OPENAI_ENDPOINTS.get(self.provider):
            base_url = os.environ.get(config.base_url_env, config.default_base_url)
            api_key = os.environ.get(config.api_key_env, config.default_api_key)
            self._check_connection(base_url, config.display_name, api_key)

    def list_models(self) -> list[str]:
        """List exact model IDs through the authenticated OpenAI-compatible client."""
        if self.provider not in _OPENAI_ENDPOINTS:
            raise ValueError("Model listing requires an OpenAI-compatible provider.")
        return [model.id for model in self._client.client.models.list()]

    @staticmethod
    def _check_connection(base_url: str, provider_name: str, api_key: str) -> None:
        """Check reachability and credentials without issuing a generation request."""
        models_url = f"{base_url.rstrip('/')}/models"
        try:
            req = urllib.request.Request(
                models_url,
                headers={
                    "User-Agent": "AAD-LLM-Connection-Check",
                    "Authorization": f"Bearer {api_key}",
                },
            )
            with urllib.request.urlopen(req, timeout=10.0):
                pass
        except Exception as e:
            raise ConnectionError(
                f"Could not connect to the {provider_name} LLM server at '{base_url}'.\n"
                f"Error details: {e}\n"
                f"Troubleshooting:\n"
                "Check the endpoint URL, API key and network/VPN access. "
                "For a local server, also check that scripts/llm.sh is running."
            ) from None

    @staticmethod
    def _get_local_model_name(base_url: str, api_key: str) -> str:
        """Queries the local server's /models endpoint to get the active model name."""
        models_url = f"{base_url.rstrip('/')}/models"
        try:
            req = urllib.request.Request(
                models_url,
                headers={
                    "User-Agent": "AAD-LLM-Model-Check",
                    "Authorization": f"Bearer {api_key}",
                },
            )
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
            model = self.kwargs.pop("model", None) or os.environ.get(
                "GEMINI_MODEL", "gemini-2.0-flash"
            )
            return Gemini_LLM(api_key=api_key, model=model, **self.kwargs)

        if config := _OPENAI_ENDPOINTS.get(self.provider):
            return self._init_openai_compatible(config, should_validate)

        raise ValueError(f"Unknown provider '{self.provider}'. Choose from: {list(Provider)}")

    def _init_openai_compatible(self, config: EndpointConfig, should_validate: bool) -> OpenAI_LLM:
        base_url = os.environ.get(config.base_url_env, config.default_base_url)
        api_key = os.environ.get(config.api_key_env, config.default_api_key)
        model = self.kwargs.pop("model", None) or os.environ.get(config.model_env)

        if not api_key:
            raise ValueError(f"Set {config.api_key_env} for {config.display_name}.")
        if self.provider == Provider.UPB and not model:
            raise ValueError("Set UPB_MODEL or pass model= with an exact gateway model ID.")

        if self.provider == Provider.UPB:
            llm = GatewayLLM(
                api_key=api_key,
                model=model,
                base_url=base_url,
                limiter=GatewayRequestLimiter.for_model(base_url, model),
                **self.kwargs,
            )
            if should_validate:
                try:
                    llm.client.models.list()
                except openai.APIError as error:
                    llm.client.close()
                    status = (
                        error.status_code
                        if isinstance(error, openai.APIStatusError)
                        else type(error).__name__
                    )
                    raise ConnectionError(
                        f"Could not connect to the {config.display_name} LLM server at '{base_url}' "
                        f"({status}). Check credentials, quota and network/VPN access."
                    ) from None
            return llm

        if should_validate:
            self._check_connection(base_url, config.display_name, api_key)
            model = model or self._get_local_model_name(base_url, api_key)
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
        session_messages: list[dict[str, str]],
        parent_ids: list[str] | None = None,
        HPO: bool = False,
        base_code: str | None = None,
        diff_mode: bool = False,
    ) -> Solution:
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
            except Exception as error:
                # GatewayLLM already owns paced network retries. Keep the existing
                # outer retries for malformed candidate output, not API failures.
                if attempt == max_retries or (
                    self.provider == Provider.UPB and isinstance(error, openai.APIError)
                ):
                    raise
                time.sleep(backoff * attempt)

    @property
    def model(self) -> ModelInfo:
        """Model identifier string wrapped as ModelInfo to allow accessing .name directly."""
        raw_model = getattr(self._client, "model", "unknown") or "unknown"
        return ModelInfo(raw_model)

    def close(self) -> None:
        """Release the network client owned by this connection."""
        self._client.client.close()

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
