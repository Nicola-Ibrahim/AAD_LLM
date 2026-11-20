"""Cross-process request pacing for OpenAI-compatible model gateways."""

import hashlib
import math
import os
import sqlite3
import tempfile
import time
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

import httpx

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
