"""Explicit provider and model identity for synthesis workflows."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModelSelection(BaseModel):
    """Select one exact model from a supported provider."""

    provider: Literal["local", "upb", "lmstudio", "gemini"]
    model_id: str = Field(min_length=1, strict=True)

    model_config = ConfigDict(frozen=True)

    @field_validator("model_id")
    @classmethod
    def require_nonblank_model_id(cls, model_id: str) -> str:
        if not model_id.strip():
            raise ValueError("Model ID must not be blank")
        return model_id
