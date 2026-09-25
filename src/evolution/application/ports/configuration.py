"""Port for loading a validated synthesis campaign configuration."""

from typing import Protocol

from evolution.application.synthesis_config import SynthesisConfig


class SynthesisConfigReader(Protocol):
    def load_config(self) -> SynthesisConfig: ...
