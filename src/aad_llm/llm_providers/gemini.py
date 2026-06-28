"""
GeminiProvider — LLaMEA connector for Google Gemini.

Usage:
    from aad_llm.llm_providers import build_llm, PROVIDER_GEMINI

    llm = build_llm(
        PROVIDER_GEMINI,
        api_key="YOUR_GEMINI_API_KEY",   # or omit and set GOOGLE_API_KEY env var
        model="gemini-2.0-flash",        # optional, this is the default
    )

Requires the google-genai package:
    uv sync --extra gemini
"""
import os

from llamea import Gemini_LLM


class GeminiProvider(Gemini_LLM):
    """
    LLaMEA-compatible connector for Google Gemini.

    Args:
        api_key (str | None): Gemini API key. Falls back to the GOOGLE_API_KEY
                              environment variable when not supplied.
        model (str): Gemini model name. Defaults to "gemini-2.0-flash".
    """

    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        **kwargs,
    ):
        resolved_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        if not resolved_key:
            raise ValueError(
                "A Gemini API key is required. "
                "Pass api_key= or set the GOOGLE_API_KEY environment variable."
            )
        super().__init__(api_key=resolved_key, model=model, **kwargs)
