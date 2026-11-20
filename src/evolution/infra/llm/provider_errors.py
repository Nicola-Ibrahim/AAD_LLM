"""Safe translation of provider SDK failures into application-facing errors."""

import openai

from evolution.application.exceptions import ProviderError


def provider_error(error: openai.APIError, model: str) -> ProviderError:
    """Translate SDK errors without copying requests, keys or response bodies."""
    status = getattr(error, "status_code", None)
    if status in {401, 403}:
        return ProviderError("authentication", model, "check gateway credentials and model access")
    if status == 402 or error.code in {
        "insufficient_quota",
        "budget_exceeded",
        "budget_exhausted",
        "billing_hard_limit_reached",
        "spend_limit_exceeded",
    }:
        return ProviderError("quota", model, "the provider quota or budget is exhausted")
    if isinstance(error, openai.APITimeoutError):
        return ProviderError("timeout", model, "the generation request timed out")
    return ProviderError("unavailable", model, f"generation failed; HTTP status {status}")
