import pickle

import numpy as np
import pytest
from llamea import LLaMEA

from evolution.application import SessionConfig
from evolution.application.synthesis.evaluate_candidate import CandidateEvaluationService
from evolution.domain.enums import SynthesisMode
from evolution.domain.vos import ProblemProfile
from evolution.infra.engines.llamea import Evaluator, LLaMEASession
from evolution.infra.engines.llamea.checkpoint import SynthesisCheckpointUnpickler
from evolution.infra.engines.llamea.prompts import SynthesisPrompts
from evolution.infra.llm.client import LLMClient, Provider
from evolution.infra.storage.code.repository import CodeRepository
from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository
from shared.domain.noise import NoNoiseStrategy
from shared.infra.database import Database
from shared.infra.database.tables import Base
from shared.infra.execution.candidate_executor import create_candidate_executor
from shared.infra.problems.bbob import BBOBProblem


def build_candidate_evaluation_service(*, problem, **kwargs):
    return CandidateEvaluationService(
        problem=problem,
        executor=create_candidate_executor(kwargs.get("timeout_seconds", 30.0)),
        **kwargs,
    )


# Mock logger
class MockLogger:
    def __init__(self, dirname):
        self.dirname = dirname
        self.attempt = 0

    def log_population(self, pop):
        pass

    def log_individual(self, ind):
        pass


@pytest.fixture
def test_repos(tmp_path):
    db_path = tmp_path / "test.db"
    database = Database(f"sqlite:///{db_path}")
    Base.metadata.create_all(database.engine)
    db_repo = SQLiteSynthesisRepository(database.session_factory)
    code_repo = CodeRepository(base_dir=tmp_path / "code")
    return db_repo, code_repo


def test_pickle_llamea(tmp_path, test_repos):
    db_repo, code_repo = test_repos
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy(), instance_id=1)
    llm = LLMClient(Provider.LOCAL)

    candidate_evaluation_service = build_candidate_evaluation_service(problem=problem, budget=10)
    evaluator = Evaluator(
        problem=problem,
        db_repo=db_repo,
        code_repo=code_repo,
        experiment_id=1,
        config=SessionConfig(budget=10),
        candidate_evaluation_service=candidate_evaluation_service,
    )
    opt = LLaMEA(f=evaluator, llm=llm, log=False)

    opt.logger = MockLogger(dirname=str(tmp_path))
    opt.pickle_archive()

    expected_path = tmp_path / "llamea_config.pkl"
    assert expected_path.exists(), "llamea_config.pkl was not created!"
    assert expected_path.stat().st_size > 0, "llamea_config.pkl is empty!"

    with open(expected_path, "rb") as f:
        loaded_opt = pickle.load(f)

    assert loaded_opt is not None
    assert loaded_opt.llm is not None
    assert isinstance(loaded_opt.llm, LLMClient)


def test_llm_client_pickling(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    wrapper = LLMClient(provider="gemini")
    assert wrapper.model == "gemini-2.0-flash"
    assert wrapper.provider == "gemini"

    data = pickle.dumps(wrapper)
    loaded = pickle.loads(data)

    assert loaded.provider == "gemini"
    assert loaded.model == "gemini-2.0-flash"
    assert loaded._client is not None


def test_warm_start_rehydration(tmp_path, test_repos):
    db_repo, code_repo = test_repos
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy(), instance_id=1)
    llm = LLMClient(Provider.LOCAL)

    problem_profile = ProblemProfile(
        problem_id=problem.problem_id,
        dim=problem.dim,
        noise_std=problem.noise_std,
        noise_model=problem.noise_model,
        instance_id=problem.instance_id,
        true_optimum=problem.true_optimum,
    )
    exp_id = db_repo.create_experiment(
        problem=problem_profile,
        mode=SynthesisMode.EXPLICIT,
        llm_name=llm.model.name,
        prompt_strategy="baseline",
        budget=1000000,
        max_iterations=5,
    )

    session = LLaMEASession(
        problem=problem,
        experiment_id=exp_id,
        initial_iteration=0,
        prompt_strategy="baseline",
        llm_client=llm,
        db_repo=db_repo,
        code_repo=code_repo,
        config=SessionConfig(iterations=5),
    )

    evaluator = session._setup_evaluator()
    prompts = SynthesisPrompts(task="task_prompt", example="example_prompt", format="format_prompt")
    synthesis_engine = session._create_synthesis_engine(evaluator, prompts)

    synthesis_engine.pickle_archive()
    config_file = session._archive_dir / "llamea_config.pkl"
    assert config_file.exists()

    resumed_engine = session._create_synthesis_engine(evaluator, prompts)
    assert resumed_engine is not None
    assert resumed_engine.generation == synthesis_engine.generation


def test_llm_client_model_resolution(monkeypatch):
    monkeypatch.setenv("LOCAL_LLM_MODEL", "qwen2.5-coder-14b-instruct-q4_k_m.gguf")
    llm_env = LLMClient(Provider.LOCAL)
    assert llm_env.model.name == "qwen2.5-coder-14b-instruct-q4_k_m.gguf"

    llm_arg = LLMClient(Provider.LOCAL, model="qwen2.5-coder-32b-instruct-q4_k_m.gguf")
    assert llm_arg.model.name == "qwen2.5-coder-32b-instruct-q4_k_m.gguf"


def test_llm_client_raises_when_server_not_running(monkeypatch):
    monkeypatch.delenv("SKIP_LLM_VALIDATION", raising=False)
    monkeypatch.setenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:59999/v1")
    with pytest.raises(ConnectionError, match="Could not connect to the local LLM server"):
        LLMClient(Provider.LOCAL)


def test_legacy_problem_checkpoint_survives_module_relocation():
    import io
    import pickle
    import sys

    original = BBOBProblem(1, 2, NoNoiseStrategy())
    legacy = pickle.dumps(original, protocol=0)
    for old, new in SynthesisCheckpointUnpickler.MODULE_RELOCATIONS.items():
        legacy = legacy.replace(new.encode(), old.encode())
    restored = SynthesisCheckpointUnpickler(io.BytesIO(legacy)).load()
    assert isinstance(restored, BBOBProblem)
    assert restored.true_optimum == original.true_optimum
    np.testing.assert_array_equal(restored.lower_bound, original.lower_bound)
    assert restored.eval_clean(np.array([1.0, -1.0])) == original.eval_clean(np.array([1.0, -1.0]))
    assert "evolution.infra.problems.bbob" not in sys.modules
