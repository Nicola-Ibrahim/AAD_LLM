"""Smoke-test diagnostics use fake HTTP responses; pytest never calls UPB."""

import json

import httpx
import pytest
from scripts import check_upb


@pytest.fixture
def fake_gateway(monkeypatch, tmp_path):
    monkeypatch.setattr(check_upb, "load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.setenv("UPB_API_KEY", "test-only-secret")
    monkeypatch.setenv("UPB_API_BASE", "https://gateway.test/v1/")
    monkeypatch.setenv("UPB_MODEL", "test-model")
    monkeypatch.setenv("UPB_REQUESTS_PER_MINUTE", "1000000")
    monkeypatch.setenv("UPB_RATE_LIMIT_STATE", str(tmp_path / "limits.sqlite3"))

    def install(handler):
        monkeypatch.setattr(
            httpx.HTTPTransport,
            "handle_request",
            lambda self, request: handler(request),
        )

    return install


def test_smoke_discovers_models_and_gets_a_short_answer(fake_gateway, capsys):
    calls = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.headers["Authorization"] == "Bearer test-only-secret"
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": "test-model"}]})
        assert request.url.path == "/v1/chat/completions"
        payload = json.loads(request.content)
        assert payload["model"] == "test-model"
        assert payload["messages"][0]["role"] == "user"
        assert "max_tokens" not in payload
        assert "temperature" in payload
        return httpx.Response(200, json={"choices": [{"message": {"content": "4"}}]})

    fake_gateway(handle)
    assert check_upb.main([]) == 0
    assert [call.method for call in calls] == ["GET", "POST"]
    output = capsys.readouterr().out
    assert "Response: 4" in output
    assert "test-only-secret" not in output


@pytest.mark.parametrize("status", [401, 403, 429, 503])
def test_failure_is_reported_once_without_dumping_secret_response_bodies(
    fake_gateway, capsys, status
):
    calls = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(status, json={"error": {"message": "test-only-secret"}})

    fake_gateway(handle)
    assert check_upb.main([]) == 1
    assert len(calls) == 1
    output = capsys.readouterr().out
    assert f"HTTP {status}" in output
    assert "test-only-secret" not in output


def test_list_only_does_not_generate(fake_gateway):
    calls = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"data": [{"id": "available-model"}]})

    fake_gateway(handle)
    assert check_upb.main(["--list-only"]) == 0
    assert len(calls) == 1
    assert calls[0].method == "GET"


def test_network_error_is_visible_and_not_retried(fake_gateway, capsys):
    def handle(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("DNS unavailable", request=request)

    fake_gateway(handle)
    assert check_upb.main([]) == 1
    assert "generation failed" in capsys.readouterr().out


def test_empty_model_output_is_distinguished_from_connection_failure(fake_gateway, capsys):
    def handle(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json={"data": [{"id": "test-model"}]})
        return httpx.Response(
            200, json={"choices": [{"finish_reason": "length", "message": {"content": ""}}]}
        )

    fake_gateway(handle)
    assert check_upb.main([]) == 1
    assert "API returned no text" in capsys.readouterr().out


def test_generation_failure_passes_through_gateway_without_retry(fake_gateway, capsys):
    calls = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"data": [{"id": "test-model"}]})
        return httpx.Response(
            429,
            headers={"Retry-After": "60"},
            json={"error": {"message": "test-only-secret"}},
        )

    fake_gateway(handle)
    assert check_upb.main([]) == 1
    assert [request.method for request in calls] == ["GET", "POST"]
    output = capsys.readouterr().out
    assert "HTTP 429" in output
    assert "test-only-secret" not in output
