"""Base domain abstractions for benchmarking."""

from pydantic import BaseModel, ConfigDict


class ValueObject(BaseModel):
    """Immutable domain concept defined entirely by its values without identity."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
