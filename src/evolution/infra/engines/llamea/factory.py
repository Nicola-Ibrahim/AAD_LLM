"""Create and release model-specific LLaMEA engines for synthesis jobs."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from evolution.application.interfaces.synthesis_engine import (
    SynthesisEngine,
    SynthesisEngineFactory,
)
from evolution.application.model_selection import ModelSelection
from evolution.domain.interfaces.code_repository import CodeRepository
from evolution.infra.engines.llamea.runner import LLaMEAEngine
from evolution.infra.llm.client import LLMClient
from shared.application.diagnostics import preserve_primary_failure


class LLaMEAEngineFactory(SynthesisEngineFactory):
    """Open a fresh provider client for the selected model and close it after use."""

    def __init__(self, code_repository: CodeRepository, checkpoint_root: Path) -> None:
        self.code_repository = code_repository
        self.checkpoint_root = checkpoint_root

    @contextmanager
    def open(self, model: ModelSelection) -> Iterator[SynthesisEngine]:
        client = LLMClient(model.provider, model=model.model_id)
        try:
            yield LLaMEAEngine(
                llm_client=client,
                code_repo=self.code_repository,
                checkpoint_root=self.checkpoint_root,
                model_id=model.model_id,
            )
        finally:
            with preserve_primary_failure("LLM client close"):
                client.close()
