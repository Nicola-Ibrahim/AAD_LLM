"""OpenAI-compatible gateway client with bounded, paced retries."""

import logging
import math
import time
from email.utils import parsedate_to_datetime
from random import SystemRandom

import httpx
import openai
from llamea import OpenAI_LLM

from evolution.application.exceptions import ProviderError
from evolution.infra.llm.provider_errors import provider_error
from evolution.infra.llm.request_limiter import GatewayRequestLimiter

logger = logging.getLogger(__name__)

# Preserve the former class lookup path for checkpoints or user-created pickles
# that serialized GatewayRequestLimiter before it moved to request_limiter.py.


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
        temperature: float | None = 0.8,
        **kwargs: object,
    ) -> None:
        super().__init__(api_key=api_key, model=model, temperature=temperature, **kwargs)
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
                    temperature=self.temperature
                    if self.temperature is not None
                    else openai.NOT_GIVEN,
                )
                choice = response.choices[0] if response.choices else None
                usage = response.usage
                logger.info(
                    "Gateway token usage for %s: input=%s cached_input=%s output=%s "
                    "reasoning=%s total=%s finish=%s",
                    self.model,
                    usage.prompt_tokens if usage else None,
                    getattr(usage.prompt_tokens_details, "cached_tokens", None) if usage else None,
                    usage.completion_tokens if usage else None,
                    getattr(usage.completion_tokens_details, "reasoning_tokens", None)
                    if usage
                    else None,
                    usage.total_tokens if usage else None,
                    choice.finish_reason if choice else None,
                    extra={"progress": True},
                )
                content = choice.message.content if choice else None
                if not content:
                    raise ProviderError("invalid_response", self.model, "the API returned no text")
                return content
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
                    raise provider_error(error, self.model) from error
                # SystemRandom must not perturb the optimizer's seeded RNG stream.
                delay = default_delay * 2**attempt + SystemRandom().uniform(0.0, 1.0)
                if isinstance(error, openai.APIStatusError):
                    delay = retry_delay(error, delay)
                self.limiter.defer(delay)
                if attempt == max_retries:
                    raise provider_error(error, self.model) from error
        raise AssertionError("Unreachable gateway retry state")
