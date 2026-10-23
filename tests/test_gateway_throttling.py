"""Shared pacing and gateway-only retry policy, using fake HTTP responses."""

import multiprocessing
import os
import pickle
import random
import time
from datetime import datetime, timezone
from email.utils import format_datetime
from queue import Empty
from unittest.mock import MagicMock

import httpx
import openai
import pytest

from evolution.infra.llm.client import LLMClient
from evolution.infra.llm.gateway import GatewayLLM, GatewayRequestLimiter, retry_delay


class Clock:
    def __init__(self) -> None:
        self.value = 1_000_000.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.value += seconds


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> Clock:
    clock = Clock()
    monkeypatch.setattr("evolution.infra.llm.gateway.time.time", clock.now)
    monkeypatch.setattr("evolution.infra.llm.gateway.time.sleep", clock.sleep)
    return clock


@pytest.mark.parametrize(
    "model,rpm",
    [
        ("gwdg.qwen3-coder-next", 8.0),
        ("kiconnect.qwen3.8-27b", 80.0),
        ("openai.gpt-4o-mini", 80.0),
    ],
)
def test_limits_follow_upstream_provider_not_cpu_count(monkeypatch, tmp_path, model, rpm):
    monkeypatch.delenv("UPB_REQUESTS_PER_MINUTE", raising=False)
    monkeypatch.setenv("UPB_RATE_LIMIT_STATE", str(tmp_path / "limits.sqlite3"))
    limiter = GatewayRequestLimiter.for_model("https://gateway.test/v1", model)
    assert limiter.requests_per_minute == rpm


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "not-a-number"])
def test_invalid_rate_is_not_silently_disabled(monkeypatch, tmp_path, value):
    monkeypatch.setenv("UPB_RATE_LIMIT_STATE", str(tmp_path / "limits.sqlite3"))
    monkeypatch.setenv("UPB_REQUESTS_PER_MINUTE", value)
    with pytest.raises(ValueError):
        GatewayRequestLimiter.for_model("https://gateway.test/v1", "gwdg.qwen")


def test_unknown_provider_requires_approved_rate(monkeypatch, tmp_path):
    monkeypatch.delenv("UPB_REQUESTS_PER_MINUTE", raising=False)
    monkeypatch.setenv("UPB_RATE_LIMIT_STATE", str(tmp_path / "limits.sqlite3"))
    with pytest.raises(ValueError, match="approved provider limit"):
        GatewayRequestLimiter.for_model("https://gateway.test/v1", "pc2.custom")
    monkeypatch.setenv("UPB_REQUESTS_PER_MINUTE", "5")
    assert (
        GatewayRequestLimiter.for_model("https://gateway.test/v1", "pc2.custom").requests_per_minute
        == 5
    )


def test_models_of_same_provider_share_gate_but_other_provider_is_independent(
    monkeypatch,
    tmp_path,
    clock,
):
    monkeypatch.delenv("UPB_REQUESTS_PER_MINUTE", raising=False)
    monkeypatch.setenv("UPB_RATE_LIMIT_STATE", str(tmp_path / "limits.sqlite3"))
    first = GatewayRequestLimiter.for_model("https://gateway.test/v1/", "gwdg.qwen")
    second = GatewayRequestLimiter.for_model("https://gateway.test/v1", "gwdg.llama")
    other = GatewayRequestLimiter.for_model("https://gateway.test/v1", "openai.example")
    request = httpx.Request("GET", "https://gateway.test/v1/models")
    first.wait(request)
    second.wait(request)
    assert clock.sleeps == [7.5]
    other.wait(request)
    assert clock.sleeps == [7.5]
    assert first.scope == second.scope != other.scope


def test_cooldown_survives_reconstruction_without_shortening_existing_delay(tmp_path, clock):
    first = GatewayRequestLimiter(tmp_path / "limits.sqlite3", "gwdg", 8.0)
    first.defer(30)
    first.defer(2)
    restored = pickle.loads(pickle.dumps(first))
    restored.wait(httpx.Request("GET", "https://gateway.test"))
    assert clock.sleeps == [30.0]


def _take_slots(limiter, queue):
    for _ in range(3):
        limiter.wait(httpx.Request("POST", "https://gateway.test/v1/chat/completions"))
        queue.put((time.time(), os.getpid()))


def test_spawned_workers_share_one_limit(tmp_path):
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    limiter = GatewayRequestLimiter(tmp_path / "limits.sqlite3", "shared", 1200.0)
    workers = [context.Process(target=_take_slots, args=(limiter, queue)) for _ in range(3)]
    try:
        for worker in workers:
            worker.start()
        try:
            starts = sorted(queue.get(timeout=30) for _ in range(9))
        except Empty:
            pytest.fail("Workers did not finish reserving request slots")
        for worker in workers:
            worker.join(timeout=10)
            assert worker.exitcode == 0
        assert len({pid for _, pid in starts}) == 3
        assert all(b[0] - a[0] >= 0.045 for a, b in zip(starts, starts[1:]))
    finally:
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
                worker.join()
        queue.close()
        queue.join_thread()


@pytest.mark.parametrize(
    "header,expected",
    [
        ({"Retry-After": "12"}, 12.0),
        ({"retry-after-ms": "250"}, 0.25),
        ({"Retry-After": "bad"}, 9.0),
        ({"Retry-After": "nan"}, 9.0),
        ({}, 9.0),
    ],
)
def test_retry_headers(header, expected):
    request = httpx.Request("POST", "https://gateway.test")
    error = openai.RateLimitError(
        "limited", response=httpx.Response(429, request=request, headers=header), body=None
    )
    assert retry_delay(error, 9.0) == expected


def test_retry_after_http_date(clock):
    request = httpx.Request("POST", "https://gateway.test")
    header = format_datetime(datetime.fromtimestamp(clock.value + 25, timezone.utc), usegmt=True)
    error = openai.RateLimitError(
        "limited",
        response=httpx.Response(429, request=request, headers={"Retry-After": header}),
        body=None,
    )
    assert retry_delay(error, 9.0) == 25


def _response(status: int) -> httpx.Response:
    if status == 200:
        return httpx.Response(
            200,
            json={
                "id": "test",
                "object": "chat.completion",
                "created": 0,
                "model": "gwdg.qwen",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "program"},
                    }
                ],
            },
        )
    return httpx.Response(
        status, headers={"Retry-After": "20"}, json={"error": {"message": "temporary limit"}}
    )


def test_every_http_retry_is_paced_and_does_not_consume_optimizer_rng(tmp_path, clock, monkeypatch):
    limiter = GatewayRequestLimiter(tmp_path / "limits.sqlite3", "shared", 8.0)
    llm = GatewayLLM("test-key", "gwdg.qwen", "https://gateway.test/v1", limiter)
    starts = []
    payloads = []
    responses = iter([_response(429), _response(200)])

    def send(self, request):
        starts.append(clock.now())
        payloads.append(request.content)
        return next(responses)

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", send)
    before = random.getstate()
    assert llm.query([{"role": "user", "content": "same prompt"}]) == "program"
    assert random.getstate() == before
    assert starts == [1_000_000, 1_000_020]
    assert payloads[0] == payloads[1]
    assert llm.client.max_retries == 0
    llm.client.close()


@pytest.mark.parametrize(
    "status,code",
    [
        (400, "bad_request"),
        (401, "invalid_api_key"),
        (403, "permission_denied"),
        (402, "budget_exceeded"),
        (429, "insufficient_quota"),
    ],
)
def test_permanent_errors_are_not_retried_by_outer_llm_wrapper(
    monkeypatch,
    tmp_path,
    status,
    code,
):
    monkeypatch.setenv("UPB_API_KEY", "test-key")
    monkeypatch.setenv("UPB_MODEL", "gwdg.qwen")
    monkeypatch.setenv("UPB_RATE_LIMIT_STATE", str(tmp_path / "limits.sqlite3"))
    wrapper = LLMClient("upb")
    probe = MagicMock(
        return_value=httpx.Response(status, json={"error": {"message": "stopped", "code": code}})
    )
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", lambda self, request: probe(request))
    with pytest.raises(openai.APIError):
        wrapper.sample_solution([{"role": "user", "content": "test"}])
    assert probe.call_count == 1
    wrapper._client.client.close()


def test_retry_count_is_bounded(tmp_path, clock, monkeypatch):
    limiter = GatewayRequestLimiter(tmp_path / "limits.sqlite3", "shared", 8.0)
    llm = GatewayLLM("test-key", "gwdg.qwen", "https://gateway.test/v1", limiter)
    probe = MagicMock(side_effect=lambda request: _response(503))
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", lambda self, request: probe(request))
    with pytest.raises(openai.InternalServerError):
        llm.query([{"role": "user", "content": "test"}], max_retries=2)
    assert probe.call_count == 3
    llm.client.close()


def test_local_provider_does_not_create_gateway_gate(tmp_path, monkeypatch):
    path = tmp_path / "must-not-exist.sqlite3"
    monkeypatch.setenv("UPB_RATE_LIMIT_STATE", str(path))
    client = LLMClient("local")
    assert not isinstance(client._client, GatewayLLM)
    assert not path.exists()
    client._client.client.close()
