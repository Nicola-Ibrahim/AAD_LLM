"""Single sessions are independently usable without campaign scheduling."""

import io
import pickle
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest
from llamea import Solution
from pydantic import ValidationError, create_model

from evolution.application.interfaces.synthesis_engine import SynthesisEngine
from evolution.application.synthesis.service import Synthesis
from evolution.application.synthesis.settings import SynthesisSettings
from evolution.infra.di import EvolutionProvider, synthesis_worker_scope
from evolution.infra.engines.llamea import LLaMEAEngine
from evolution.infra.engines.llamea.checkpoint import SynthesisCheckpointUnpickler
from evolution.infra.llm.client import LLMClient
from evolution.infra.logging import SynthesisLogger
from evolution.infra.storage.code.repository import CodeRepository
from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository
from shared.infra.di import container_scope
from shared.infra.problems.factory import BBOBProblemFactory


class GeneratedModel:
    def __init__(self):
        self.model = SimpleNamespace(name="connected-test-model")

    def sample_solution(self, *args, **kwargs):
        return Solution(
            name="Optimizer",
            code="""import numpy as np
class Optimizer:
    def __init__(self, dim):
        self.dim = dim
    def __call__(self, problem, budget):
        x = np.zeros(self.dim)
        return x, float(problem(x))
""",
        )


def parameters():
    return dict(
        problem_id=1,
        dim=2,
        noise_std=0.0,
        noise_model="none",
        mode="explicit",
        prompt_strategy="baseline",
        budget=10,
        iterations=2,
        timeout_seconds=30.0,
        synthesis_seed=43,
    )


def test_single_session_creates_one_experiment_without_a_campaign(db_session_factory, tmp_path):
    repository = SQLiteSynthesisRepository(db_session_factory)
    engine = LLaMEAEngine(GeneratedModel(), CodeRepository(tmp_path / "code"))
    session = Synthesis(engine, repository, SynthesisLogger(), BBOBProblemFactory())
    result = session.run(**parameters())
    (stored,) = repository.load_by_ids([result.experiment_id])
    assert engine.model_name == stored.llm_name == "connected-test-model"
    assert stored.status == "completed"
    assert stored.problem.instance_id == 1
    assert stored.synthesis_seed == 43
    assert stored.budget == 10
    assert stored.max_iterations == len(stored.iterations) == 2


@pytest.mark.parametrize(
    "change",
    [
        {"budget": 0},
        {"dim": 0},
        {"instance_id": 0},
        {"noise_std": -0.1},
        {"mode": "unknown"},
        {"prompt_strategy": "unknown"},
    ],
)
def test_invalid_single_session_does_not_create_records(change):
    repository = MagicMock()
    factory = MagicMock()
    session = Synthesis(MagicMock(), repository, SynthesisLogger(), factory)
    with pytest.raises((ValueError, ValidationError)):
        session.run(**(parameters() | change))
    factory.create.assert_not_called()
    repository.create_experiment.assert_not_called()


def test_single_session_is_resolvable_without_a_worker_context(monkeypatch):
    import shared.infra.di as composition

    monkeypatch.setattr(composition, "Database", MagicMock())
    client = MagicMock()
    with container_scope(
        EvolutionProvider(), context={LLMClient: client}, request_context={}
    ) as scope:
        session = scope.get(Synthesis)
        assert session.engine is scope.get(SynthesisEngine)
        assert session.engine is scope.get(LLaMEAEngine)
        assert session.engine.llm_client is client


def test_worker_session_never_constructs_another_client(monkeypatch):
    import evolution.infra.di as composition
    import shared.infra.di as shared_composition

    monkeypatch.setattr(shared_composition, "Database", MagicMock())
    client_factory = MagicMock(side_effect=AssertionError("worker opened a new LLM connection"))
    monkeypatch.setattr(composition, "LLMClient", client_factory)
    engine = MagicMock(spec=SynthesisEngine)
    with synthesis_worker_scope(engine) as session:
        assert session.engine is engine
    client_factory.assert_not_called()


@pytest.mark.parametrize(
    "module_name,class_name",
    [
        ("evolution.application.synthesis.models", "SessionConfig"),
        ("evolution.application.synthesis.session_types", "SynthesisSessionSettings"),
    ],
)
def test_historical_session_settings_load_without_old_import_modules(
    monkeypatch, module_name, class_name
):
    module = ModuleType(module_name)
    legacy = create_model(class_name, __base__=SynthesisSettings, __module__=module_name)
    setattr(module, class_name, legacy)
    monkeypatch.setitem(sys.modules, module_name, module)
    payload = pickle.dumps(legacy(budget=1_000_000, iterations=7))
    monkeypatch.delitem(sys.modules, module_name)
    restored = SynthesisCheckpointUnpickler(io.BytesIO(payload)).load()
    assert type(restored) is SynthesisSettings
    assert restored.budget == 1_000_000
    assert restored.iterations == 7
    assert module_name not in sys.modules


def test_internal_session_budget_must_be_explicit():
    with pytest.raises(ValidationError):
        SynthesisSettings()
