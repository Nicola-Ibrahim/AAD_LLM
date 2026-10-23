"""UPB request pacing shared by local worker processes, independent of CPU scheduling."""

import hashlib
import math
import os
import sqlite3
import tempfile
import time
from contextlib import closing
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from pathlib import Path
from random import SystemRandom

import httpx
import openai
from llamea import OpenAI_LLM

# Published per-person provider limits, with 20% headroom for other account use.
DEFAULT_RPM = {"gwdg": 8.0, "kiconnect": 80.0, "openai": 80.0}


@dataclass(frozen=True, slots=True)
class GatewayRequestLimiter:
    """A small runtime-only SQLite gate: no research DB, credentials or experiments."""

    state_path: Path
    scope: str
    requests_per_minute: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.requests_per_minute) or self.requests_per_minute <= 0:
            raise ValueError("UPB_REQUESTS_PER_MINUTE must be a finite positive number.")
        self.state_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with closing(sqlite3.connect(self.state_path, timeout=30)) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS requests (scope TEXT PRIMARY KEY, next_start REAL NOT NULL)"
            )
            connection.commit()

    @classmethod
    def for_model(cls, base_url: str, model: str) -> "GatewayRequestLimiter":
        provider = model.partition(".")[0]
        override = os.environ.get("UPB_REQUESTS_PER_MINUTE")
        if override is None and provider not in DEFAULT_RPM:
            raise ValueError(
                f"No published request limit configured for '{provider}'. "
                "Set UPB_REQUESTS_PER_MINUTE to your approved provider limit."
            )
        rpm = float(override) if override is not None else DEFAULT_RPM[provider]
        user_id = hashlib.sha256(str(Path.home()).encode()).hexdigest()[:16]
        default_path = Path(tempfile.gettempdir()) / f"aad-llm-{user_id}" / "request_limits.sqlite3"
        state_path = Path(os.environ.get("UPB_RATE_LIMIT_STATE", str(default_path)))
        # Different models/keys of one provider share a per-person limit.
        scope = hashlib.sha256(f"{base_url.rstrip('/')}|{provider}".encode()).hexdigest()
        return cls(state_path, scope, rpm)

    def wait(self, request: httpx.Request) -> None:
        """Reserve a request start atomically; never hold a DB lock while sleeping."""
        while True:
            with closing(sqlite3.connect(self.state_path, timeout=30)) as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT next_start FROM requests WHERE scope = ?", (self.scope,)
                ).fetchone()
                now = time.time()
                delay = max(0.0, row[0] - now) if row else 0.0
                if delay == 0.0:
                    connection.execute(
                        "INSERT INTO requests VALUES (?, ?) "
                        "ON CONFLICT(scope) DO UPDATE SET next_start = excluded.next_start",
                        (self.scope, now + 60.0 / self.requests_per_minute),
                    )
                connection.commit()
            if delay == 0.0:
                return
            # Recheck shared cooldowns and permit interrupts during long waits.
            time.sleep(min(delay, 60.0))

    def defer(self, seconds: float) -> None:
        """A provider's retry delay applies to every worker using that provider."""
        with closing(sqlite3.connect(self.state_path, timeout=30)) as connection:
            connection.execute(
                "INSERT INTO requests VALUES (?, ?) "
                "ON CONFLICT(scope) DO UPDATE SET next_start = MAX(next_start, excluded.next_start)",
                (self.scope, time.time() + seconds),
            )
            connection.commit()


def retry_delay(error: openai.APIStatusError, fallback: float) -> float:
    """Support Retry-After seconds/HTTP dates and the SDK's millisecond header."""
    headers = error.response.headers
    raw = headers.get("retry-after-ms") or headers.get("retry-after")
    if raw is None:
        return fallback
    try:
        delay = float(raw) / (1000.0 if "retry-after-ms" in headers else 1.0)
    except ValueError:
        try:
            delay = parsedate_to_datetime(raw).timestamp() - time.time()
        except (TypeError, ValueError, OverflowError):
            return fallback
    return max(0.0, delay) if math.isfinite(delay) else fallback


class GatewayLLM(OpenAI_LLM):
    """Keep LLaMEA's parsing/prompts; own one bounded, paced gateway retry loop."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        limiter: GatewayRequestLimiter,
        **kwargs: object,
    ) -> None:
        super().__init__(api_key=api_key, model=model, **kwargs)
        self.limiter = limiter
        self.client.close()
        self.base_url = base_url
        self._client_kwargs.update(
            base_url=base_url,
            max_retries=0,
            http_client=httpx.Client(
                timeout=httpx.Timeout(600.0, connect=5.0),
                follow_redirects=False,
                event_hooks={"request": [limiter.wait]},
            ),
        )
        self.client = openai.OpenAI(**self._client_kwargs)

    def query(
        self,
        session_messages: list[dict[str, str]],
        max_retries: int = 3,
        default_delay: int = 10,
    ) -> str:
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=session_messages,
                    temperature=self.temperature,
                )
                return response.choices[0].message.content or ""
            except openai.APIError as error:
                exhausted = error.code in {
                    "insufficient_quota",
                    "budget_exceeded",
                    "budget_exhausted",
                    "billing_hard_limit_reached",
                    "spend_limit_exceeded",
                }
                retryable = isinstance(error, (openai.APIConnectionError, openai.RateLimitError))
                if isinstance(error, openai.APIStatusError):
                    retryable = error.status_code in {408, 409, 429} or error.status_code >= 500
                if exhausted or not retryable:
                    raise
                # SystemRandom must not perturb the optimizer's seeded RNG stream.
                delay = default_delay * 2**attempt + SystemRandom().uniform(0.0, 1.0)
                if isinstance(error, openai.APIStatusError):
                    delay = retry_delay(error, delay)
                self.limiter.defer(delay)
                if attempt == max_retries:
                    raise
        raise AssertionError("Unreachable gateway retry state")
