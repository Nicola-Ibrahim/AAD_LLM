"""Gateway integration uses LLaMEA's existing adapter without live generation calls."""

import io
import json
import pickle
from unittest.mock import MagicMock

import httpx
import openai
import pytest

from evolution.infra.llm.client import LLMClient, Provider


@pytest.fixture
def gateway_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("UPB_API_KEY", "test-private-key")
    monkeypatch.setenv("UPB_API_BASE", "https://ai-gateway.uni-paderborn.de/v1/")
    monkeypatch.setenv("UPB_MODEL", "gwdg.qwen3-30b-a3b-instruct-2507")
    monkeypatch.setenv("UPB_RATE_LIMIT_STATE", str(tmp_path / "requests.sqlite3"))
    monkeypatch.setenv("UPB_REQUESTS_PER_MINUTE", "60000")


@pytest.fixture
def gateway_probe(monkeypatch):
    probe = MagicMock(return_value=httpx.Response(200, json={"object": "list", "data": []}))
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", lambda self, request: probe(request))
    return probe


def test_gateway_validation_sends_authentication(gateway_env, gateway_probe, monkeypatch) -> None:
    monkeypatch.delenv("SKIP_LLM_VALIDATION", raising=False)
    llm = LLMClient("upb", temperature=0.4)
    request = gateway_probe.call_args.args[0]
    assert str(request.url) == "https://ai-gateway.uni-paderborn.de/v1/models"
    assert request.headers["Authorization"] == "Bearer test-private-key"
    assert llm._client.temperature == 0.4
    assert str(llm._client.client.base_url) == "https://ai-gateway.uni-paderborn.de/v1/"
    assert llm.model == "gwdg.qwen3-30b-a3b-instruct-2507"
    llm.validate_connection()
    assert gateway_probe.call_count == 2


def test_gateway_model_listing_uses_sdk_authentication(gateway_env) -> None:
    llm = LLMClient("upb")
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "object": "list",
                "data": [
                    {
                        "id": "gwdg.qwen3-coder-next",
                        "object": "model",
                        "created": 0,
                        "owned_by": "gwdg",
                    },
                ],
            },
        )

    llm._client.client.close()
    with openai.OpenAI(
        api_key="test-private-key",
        base_url="https://ai-gateway.uni-paderborn.de/v1/",
        http_client=httpx.Client(transport=httpx.MockTransport(handle)),
    ) as client:
        llm._client.client = client
        assert llm.list_models() == ["gwdg.qwen3-coder-next"]
    assert requests[0].headers["Authorization"] == "Bearer test-private-key"
    assert requests[0].method == "GET"
    assert requests[0].url.path == "/v1/models"


@pytest.mark.parametrize("setting", ["UPB_MODEL", "UPB_API_KEY"])
def test_gateway_requires_explicit_credentials_and_model(gateway_env, monkeypatch, setting) -> None:
    monkeypatch.delenv(setting)
    with pytest.raises(ValueError, match=setting):
        LLMClient("upb")


def test_gateway_does_not_discover_first_model(gateway_env, gateway_probe, monkeypatch) -> None:
    monkeypatch.delenv("SKIP_LLM_VALIDATION", raising=False)
    monkeypatch.delenv("UPB_MODEL")
    with pytest.raises(ValueError, match="exact gateway model ID"):
        LLMClient("upb")
    gateway_probe.assert_not_called()


def test_gateway_authentication_failure_is_clear(gateway_env, gateway_probe, monkeypatch) -> None:
    monkeypatch.delenv("SKIP_LLM_VALIDATION", raising=False)
    gateway_probe.return_value = httpx.Response(401, json={"error": {"message": "Unauthorized"}})
    with pytest.raises(ConnectionError, match="401") as failure:
        LLMClient("upb")
    assert "test-private-key" not in str(failure.value)


def test_local_model_discovery_still_works_and_sends_auth(monkeypatch) -> None:
    monkeypatch.delenv("SKIP_LLM_VALIDATION", raising=False)
    monkeypatch.delenv("LOCAL_LLM_MODEL")
    monkeypatch.setenv("LOCAL_LLM_API_KEY", "local-key")
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(
        {
            "data": [{"id": "local-active-model"}],
        }
    ).encode()
    probe = MagicMock(return_value=response)
    monkeypatch.setattr("urllib.request.urlopen", probe)
    llm = LLMClient("local")
    assert llm.model == "local-active-model"
    assert probe.call_count == 2
    assert all(
        call.args[0].get_header("Authorization") == "Bearer local-key"
        for call in probe.call_args_list
    )


def test_gateway_worker_pickle_restores_model_and_endpoint_without_embedding_key(
    gateway_env,
) -> None:
    llm = LLMClient(Provider.UPB)
    serialized = pickle.dumps(llm)
    assert b"test-private-key" not in serialized
    restored = pickle.load(io.BytesIO(serialized))
    assert restored.model == llm.model
    assert restored.provider == Provider.UPB
    assert str(restored._client.client.base_url) == "https://ai-gateway.uni-paderborn.de/v1/"
    assert restored._client.client.api_key == "test-private-key"
    assert restored._client.limiter.scope == llm._client.limiter.scope
    assert restored._client.limiter.state_path == llm._client.limiter.state_path
