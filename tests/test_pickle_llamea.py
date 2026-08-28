import pickle

import pytest
from llamea import LLaMEA
from sqlalchemy.orm import sessionmaker

from evolution.application.synthesis.evaluator import Evaluator
from evolution.application.synthesis.session import LLaMEASession
from evolution.domain.services.noise_strategy import NoNoiseStrategy
from evolution.domain.vos import ProblemProfile
from evolution.infra.llm.client import LLMClient, Provider
from evolution.infra.problems.bbob import BBOBProblem
from evolution.infra.storage.code.repository import CodeRepository
from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository
from shared.database import build_engine
from shared.tables import Base


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
    engine = build_engine(db_path)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    db_repo = SQLiteSynthesisRepository(session_factory)
    code_repo = CodeRepository(base_dir=tmp_path / "code")
    return db_repo, code_repo


def test_pickle_llamea(tmp_path, test_repos):
    db_repo, code_repo = test_repos
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy(), instance_id=1)
    llm = LLMClient(Provider.LOCAL, skip_validation=True)

    evaluator = Evaluator(problem=problem, db_repo=db_repo, code_repo=code_repo, budget=10)
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
    wrapper = LLMClient(provider="gemini", skip_validation=True)
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
    llm = LLMClient(Provider.LOCAL, skip_validation=True)

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
        mode=problem.mode,
        llm_name=llm.model.name,
        prompt_strategy="baseline",
        budget=1000000,
        iterations=5,
    )

    session = LLaMEASession(
        problem=problem,
        experiment_id=exp_id,
        initial_iteration=0,
        prompt_strategy="baseline",
        llm_client=llm,
        db_repo=db_repo,
        code_repo=code_repo,
        iterations=5,
    )

    evaluator = session._setup_evaluator()
    synthesis_engine = session._create_synthesis_engine(evaluator, "task_prompt")

    synthesis_engine.pickle_archive()
    config_file = session._archive_dir / "llamea_config.pkl"
    assert config_file.exists()

    resumed_engine = session._create_synthesis_engine(evaluator, "task_prompt")
    assert resumed_engine is not None
    assert resumed_engine.generation == synthesis_engine.generation
