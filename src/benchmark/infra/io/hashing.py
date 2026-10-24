"""Hashing utilities for code integrity and caching."""

import hashlib
from pathlib import Path


def compute_code_hash(code_input: str | Path) -> str:
    """Compute SHA-256 hash of a python code string or code file path."""
    if isinstance(code_input, Path):
        if not code_input.exists():
            return ""
        code_str = code_input.read_text(encoding="utf-8")
    else:
        code_str = str(code_input)
    return hashlib.sha256(code_str.strip().encode("utf-8")).hexdigest()
