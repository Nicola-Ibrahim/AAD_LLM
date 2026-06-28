"""
Base interface documentation for LLM providers.

All providers in this package sub-class llamea.LLM (directly or via one of its
concrete sub-classes such as OpenAI_LLM / Gemini_LLM).

llamea.LLM already defines the full protocol:
  - __init__(self, api_key, model, base_url, ...)
  - query(self, session_messages) -> str
  - sample_solution(...)
  - extract_algorithm_code(...)
  - extract_algorithm_description(...)
  - set_logger(logger)

This file exists purely as a readable reference. No runtime logic lives here.
"""
from llamea.llm import LLM  # re-export so callers can use aad_llm.llm_providers.base.LLM


__all__ = ["LLM"]
