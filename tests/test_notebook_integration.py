"""Test execution of consolidated 5-notebook pipeline to ensure zero errors and data integrity."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pandas as pd
from study_fixtures import run_parameters, synthesis_config

from benchmark.application.benchmark_config import BenchmarkConfig
from benchmark.application.select_champions import ChampionSelectionService
from benchmark.application.trials.coordinator import BenchmarkCoordinator
from benchmark.application.trials.runner import BenchmarkTrialRunner
from benchmark.application.trials.workload import BenchmarkWorkload
from benchmark.domain.services.hypothesis import HypothesisTestingEngine
from benchmark.infra.io.code_reader import FilesystemCodeReader
from benchmark.infra.solvers.baselines import get_baseline_runner
from benchmark.infra.storage.model_registry import configured_model_names
from evolution.infra.concurrency.runner import ProcessPoolRunner
from evolution.infra.concurrency.worker import run_synthesis_worker
from shared.config import PROJECT_ROOT
from shared.infra.execution.candidate_executor import create_candidate_executor
from shared.infra.problems.factory import BBOBProblemFactory


def build_benchmark_service(**kwargs):
    project_root = kwargs.pop("project_root", PROJECT_ROOT)
    config = kwargs.pop("config")
    selection = ChampionSelectionService(kwargs.pop("champions_repo"))
    state = kwargs.pop("state_repo")
    logger = kwargs.pop("logger")
    code_reader = FilesystemCodeReader(project_root)
    names = configured_model_names()
    workload = BenchmarkWorkload(
        sqlite_repo=kwargs.pop("sqlite_repo"),
        champion_selection=selection,
        state_repo=state,
        code_reader=code_reader,
        model_names=names,
        **kwargs,
    )
    trials = BenchmarkTrialRunner(
        state_repo=state,
        logger=logger,
        problem_factory=BBOBProblemFactory(),
        executor_factory=create_candidate_executor,
        baseline_resolver=get_baseline_runner,
        code_reader=code_reader,
        model_names=names,
    )
    return SimpleNamespace(
        service=BenchmarkCoordinator(
            workload=workload,
            trials=trials,
            baseline_labels=config.baseline_labels,
            logger=logger,
        ),
        workload=workload,
        trials=trials,
        config=config,
    )


def test_nb00_prompts_pipeline():
    """Verify Notebook 00 (00_prompts.ipynb: Prompts & Diagnostic Feedback Inspection)."""
    from evolution.application.synthesis.evaluate_candidate import CandidateEvaluationService
    from evolution.domain.enums import PromptStrategy, SynthesisMode
    from evolution.infra.engines.llamea.prompts import (
        META_FEEDBACK_DIVERSITY_INJECTION,
        FeedbackRenderer,
        build_example_prompt,
        build_format_prompt,
        build_task_prompt,
    )
    from shared.domain.noise import HeteroscedasticNoiseStrategy, NoNoiseStrategy
    from shared.infra.problems.bbob import BBOBProblem

    # 1. Prompt generation
    prob_clean = BBOBProblem(1, 2, NoNoiseStrategy(), 1)
    prob_noisy = BBOBProblem(1, 2, HeteroscedasticNoiseStrategy(0.05), 1)

    task_p = build_task_prompt(
        prob_noisy, mode=SynthesisMode.EXPLICIT, strategy=PromptStrategy.GUIDED, budget_hint=2000
    )
    format_p = build_format_prompt()
    example_p = build_example_prompt()

    assert "BBOB function ID: 1" in task_p
    assert "class AlgorithmName:" in example_p
    assert "Respond with EXACTLY the following format" in format_p

    # 2. Feedback renderer
    renderer = FeedbackRenderer()
    clean_fb = renderer.render_success(final_error=0.0012, problem=prob_clean)
    noisy_fb = renderer.render_success(final_error=0.8250, problem=prob_noisy)
    assert "[RESULT]" in clean_fb and "0.0012" in clean_fb
    assert "[RESULT]" in noisy_fb and "0.8250" in noisy_fb

    # 3. Failure feedback & code context extraction
    tb_str = 'Traceback (most recent call last):\n  File "<string>", line 4, in __call__\n    inv_cov = np.linalg.inv(cov)\nValueError: Matrix is singular'
    code = "import numpy as np\nclass Opt:\n  def __call__(self, p, b):\n    inv_cov = np.linalg.inv(cov)\n    return x, y"
    code_ctx = CandidateEvaluationService.extract_code_context(tb_str, code)
    assert "line   4" in code_ctx
    assert "inv_cov" in code_ctx

    fail_fb = renderer.render_failure(
        error_type="ValueError",
        error_message="Matrix is singular",
        problem=prob_noisy,
        code_context=code_ctx,
    )
    assert "[RUNTIME ERROR]" in fail_fb
    assert "[NOISY PROBLEM CONTEXT]" in fail_fb
    assert "META-FEEDBACK" in META_FEEDBACK_DIVERSITY_INJECTION
    print("✅ NB00 prompts pipeline verified.")


def test_nb01_noise_pipeline():
    """Verify Notebook 01 (01_noise.ipynb: Noise Landscape & Problem Evaluation)."""
    from shared.domain.noise import HeteroscedasticNoiseStrategy
    from shared.infra.problems.bbob import BBOBProblem

    p = BBOBProblem(problem_id=1, dim=2, noise_strategy=HeteroscedasticNoiseStrategy(0.05))
    val = p([0.0, 0.0])
    assert isinstance(val, float)
    print("✅ NB01 noise pipeline verified.")


def test_nb02_synthesis_pipeline(tmp_path: Path):
    """Verify Notebook 02 (02_synthesis.ipynb: Evolutionary Synthesis Campaign Use Case & Task Construction)."""
    from evolution.application import SynthesisCampaignCoordinator
    from evolution.application.interfaces.logger import BaseLogger
    from evolution.infra.engines.llamea import LLaMEAEngine
    from evolution.infra.llm.client import LLMClient
    from evolution.infra.logging import SynthesisLogger
    from evolution.infra.storage.code.repository import CodeRepository
    from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository
    from shared.infra.database import Database
    from shared.infra.database.tables import Base

    # Exercise the notebook workflow against a fresh schema, not historical data.
    database = Database(f"sqlite:///{tmp_path / 'synthesis.db'}")
    Base.metadata.create_all(database.engine)
    sqlite_repo = SQLiteSynthesisRepository(database.session_factory)
    config = synthesis_config()
    llm = LLMClient("local")
    logger = SynthesisLogger(verbose=False)
    engine = LLaMEAEngine(llm_client=llm, code_repo=CodeRepository())

    campaign_usecase = SynthesisCampaignCoordinator(
        worker_count=1,
        sqlite_repo=sqlite_repo,
        model_name=llm.model.name,
        logger=logger,
        engine=engine,
        problem_factory=BBOBProblemFactory(),
        dispatcher=ProcessPoolRunner(max_workers=1),
        worker_fn=run_synthesis_worker,
    )
    campaign_usecase_planner = campaign_usecase._build_planner(config)

    assert campaign_usecase_planner.sqlite_repo is sqlite_repo
    assert campaign_usecase_planner.config.budget == 100_000
    assert campaign_usecase.model_name == llm.model.name
    assert campaign_usecase.logger is logger
    assert isinstance(campaign_usecase.logger, BaseLogger)
    assert hasattr(campaign_usecase_planner.auditor, "audit_matrix")
    assert hasattr(campaign_usecase_planner, "build_tasks")
    assert hasattr(campaign_usecase, "run_campaign")

    cfg = config
    assert cfg.matrix_conditions
    assert set(cfg.problem_ids) == {condition.problem_id for condition in cfg.matrix_conditions}
    assert set(cfg.dimensions) == {condition.dim for condition in cfg.matrix_conditions}
    assert cfg.budget == 100_000

    matrix_df, summary = campaign_usecase_planner.auditor.audit_matrix()
    assert not matrix_df.empty
    assert isinstance(matrix_df.index, pd.MultiIndex)
    assert list(matrix_df.index.names) == ["Problem", "Dimension", "Environment", "Strategy"]
    assert "Target Runs" in matrix_df.columns
    assert "Completed" in matrix_df.columns
    assert "Status" in matrix_df.columns
    assert "total_conditions" in summary
    assert "problem_targets" in summary

    tasks = campaign_usecase_planner.build_tasks()
    assert len(tasks) > 0

    print(f"✅ NB02 evolutionary synthesis pipeline verified ({len(tasks)} tasks constructed).")


def test_nb03_benchmark_pipeline(tmp_path, db_session_factory):
    """Verify Notebook 03 (03_benchmark.ipynb: Champion Selection + Evaluations Audit & Dispatch)."""
    print("Testing NB03 logic with ChampionSelectionService & BenchmarkCoordinator...")
    from benchmark.infra.storage import (
        ChampionsReadRepository,
        SQLiteSynthesisReadRepository,
    )
    from shared.infra.database.tables import ExperimentORM, IterationORM

    session_factory = db_session_factory
    candidate_path = tmp_path / "candidate.py"
    candidate_path.write_text("# Isolated champion-selection fixture; not executed.\n")
    with session_factory() as session:
        experiment = ExperimentORM(
            problem_id=1,
            dim=2,
            mode="explicit",
            llm_name="fixture-model",
            noise_std=0.0,
            noise_model="none",
            prompt_strategy="baseline",
            budget=100_000,
            status="completed",
        )
        session.add(experiment)
        session.flush()
        session.add(
            IterationORM(
                experiment_id=experiment.id,
                algorithm_name="FixtureOptimizer",
                final_error=0.0,
                raw_fitness=0.0,
                evaluations_used=10,
                code_path=str(candidate_path),
            )
        )
        session.commit()
    sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
    champions_repo = ChampionsReadRepository(session_factory)
    champ_service = ChampionSelectionService(champions_repo=champions_repo)
    summary, total = sqlite_repo.get_experiment_balance()
    assert total >= 0
    print(f"  • Completed experiments: {total}")

    if total > 0:
        champions = champ_service.get_champions()
        assert len(champions) > 0, "No champions found!"
        total_champs = sum(len(v) for v in champions.values())
        print(f"  • Champions discovered: {total_champs} across {len(champions)} models")
    else:
        print(
            "  • Database in fresh/running state (0 completed experiments). Balance query contract validated."
        )

    from benchmark.infra.io.trace_repository import BenchmarkStateRepository
    from benchmark.infra.logging import BenchmarkLogger

    state_repo = BenchmarkStateRepository(benchmark_dir=tmp_path / "traces")
    config = BenchmarkConfig()
    logger = BenchmarkLogger()

    benchmark_service = build_benchmark_service(
        sqlite_repo=sqlite_repo,
        champions_repo=champions_repo,
        state_repo=state_repo,
        config=config,
        logger=logger,
    )
    champions_path = tmp_path / "benchmark" / "champions.json"
    champ_service.export_champions(champions_path)
    assert champions_path.exists(), "champions.json does not exist!"
    with open(champions_path, "r", encoding="utf-8") as f:
        champions_raw = json.load(f)
    champions_flat = benchmark_service.workload.champion_selection.flatten_champions(champions_raw)
    assert len(champions_flat) > 0

    df_audit = benchmark_service.workload.audit_champions_workload(config=benchmark_service.config)
    assert not df_audit.empty
    print(f"  • Audited champions count: {len(df_audit)}")
    print("✅ NB03 benchmark evaluation pipeline verified.")


def test_nb03_import_order_isolation():
    import subprocess
    import sys

    code = (
        "from benchmark.infra.io.trace_repository import BenchmarkStateRepository; "
        "from benchmark.infra.storage import ChampionsReadRepository; "
        "from benchmark.application.trials.coordinator import BenchmarkCoordinator; "
        "from benchmark.application.benchmark_config import BenchmarkConfig; "
        "assert BenchmarkConfig().trials_per_condition == 20"
    )
    subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)


def test_nb04_audit_pipeline():
    """Verify Notebook 04 (04_audit.ipynb: Experimental Matrix Audit)."""
    from benchmark.application.trials.audit import BenchmarkAuditService
    from benchmark.infra.di import BenchmarkProvider
    from shared.infra.di import container_scope

    with container_scope(BenchmarkProvider(), context={}, request_context={}) as scope:
        snapshot = scope.get(BenchmarkAuditService).get_audit_data()
    assert isinstance(snapshot.benchmarks, pd.DataFrame)
    assert isinstance(snapshot.synthesis_gaps, pd.DataFrame)
    assert snapshot.coverage_summary.total_cells >= 0
    assert isinstance(snapshot.completed_models, tuple)


def test_statistical_analysis_pipeline(tmp_path, db_session_factory):
    """Verify shared statistical calculations and analysis data access."""
    print("\nTesting statistical analysis data access...")
    from benchmark.infra.io.trace_repository import IOHTraceReader
    from benchmark.infra.storage import SQLiteSynthesisReadRepository

    session_factory = db_session_factory
    sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
    trace_root = tmp_path / "ioh_traces"
    for solver, terminal in [("pso", 1), ("de", 3)]:
        folder = trace_root / "2D/std_0.0/f1" / solver
        folder.mkdir(parents=True)
        (folder / "trace.dat").write_text(
            f"evaluations raw_y\n1 10\n2 {terminal}\nevaluations raw_y\n1 10\n2 {terminal + 1}\n"
        )
        (folder / "IOHprofiler_f1.json").write_text(
            json.dumps(
                {
                    "function_id": 1,
                    "scenarios": [{"dimension": 2, "path": "trace.dat"}],
                }
            )
        )
    trace_repo = IOHTraceReader(trace_root)

    df_exp, df_iter = sqlite_repo.get_synthesis_dataframes()
    all_benchmark_data = trace_repo.load_benchmark_traces(
        solver_resolver=configured_model_names().resolve_folder_solver_name
    )
    assert len(all_benchmark_data) > 0
    print(f"  • Problem conditions loaded: {len(all_benchmark_data)}")

    df_omnibus = HypothesisTestingEngine().run_omnibus_kruskal(all_benchmark_data)
    df_pairwise = HypothesisTestingEngine().run_pairwise_fdr(all_benchmark_data, alpha=0.05)
    assert not df_omnibus.empty
    assert not df_pairwise.empty
    print(f"  • Omnibus tests: {len(df_omnibus)} rows")
    print(f"  • Pairwise tests (FDR-corrected): {len(df_pairwise)} rows")

    print("✅ Statistical analysis calculations verified.")


def test_synthesis_explicit_matrix_preserves_problem_dimensions_and_mode_order():
    config = synthesis_config(
        problem_targets=[{"id": 1, "dimensions": [2, 5]}, {"id": 8, "dimensions": [3]}],
        noise_conditions=[{"std": 0.0, "noise_model": "none"}],
        synthesis_modes=[
            {"mode": mode, "strategies": ["baseline"]} for mode in ["explicit", "implicit"]
        ],
    )
    assert [(c.problem_id, c.dim, c.mode.value) for c in config.matrix_conditions] == [
        (1, 2, "explicit"),
        (1, 2, "implicit"),
        (1, 5, "explicit"),
        (1, 5, "implicit"),
        (8, 3, "explicit"),
        (8, 3, "implicit"),
    ]
    assert config.dimensions == [2, 3, 5]


def test_custom_minimal_base_logger():
    """Verify that any new custom logger only needs to implement info, warning, error.

    All domain telemetry methods (header, task_start, generation, resuming, cached,
    stagnation_warning, task_complete, audit_summary, summary, success) execute without
    errors and route to the core logging methods.
    """
    from evolution.application.interfaces.logger import BaseLogger

    class MinimalLogger(BaseLogger):
        def __init__(self, verbose: bool = True):
            super().__init__(verbose=verbose)
            self.logs: list[tuple[str, str]] = []

        def info(self, msg: str) -> None:
            self.logs.append(("INFO", msg))

        def warning(self, msg: str) -> None:
            self.logs.append(("WARNING", msg))

        def error(self, msg: str) -> None:
            self.logs.append(("ERROR", msg))

    logger = MinimalLogger(verbose=True)
    assert logger.verbose is True

    # Test all domain telemetry methods without overriding them
    logger.header("Test Header", subtitle="Test Sub")
    logger.task_start(1, 10, "test-model", 2, 0.05, 1, "baseline", 101)
    logger.generation(1, 10, "Algo1", error=0.01, fitness=-0.01, evals_used=100, runtime=1.5)
    logger.generation(
        2,
        10,
        "Algo2",
        error=None,
        fitness=None,
        evals_used=0,
        runtime=0.5,
        is_failure=True,
        failure_reason="SyntaxError",
    )
    logger.resuming(101, 2, 10)
    logger.cached(101, 10, 0.005)
    logger.stagnation_warning(3, 3)
    logger.task_complete(101, "Algo1", 0.01, raw_obj=0.01, true_opt=0.0)
    logger.audit_summary("test-model", 10, 5, 4, 1, 50.0)
    logger.summary("Test Summary", {"Metric1": 100, "Metric2": "Pass"})
    logger.success("All tasks finished successfully")

    # Assert that all calls were routed to info and warning
    info_logs = [msg for level, msg in logger.logs if level == "INFO"]
    warn_logs = [msg for level, msg in logger.logs if level == "WARNING"]

    assert len(info_logs) >= 9
    assert len(warn_logs) >= 1
    assert any("TEST HEADER" in m for m in info_logs)
    assert any("Stagnation warning" in m for m in warn_logs)
    assert any("[SUCCESS]" in m for m in info_logs)


def test_campaign_usecase_run_worker_and_campaign():
    """Verify SynthesisCampaignCoordinator run_worker and run_campaign methods."""
    from unittest.mock import patch

    from evolution.application import SessionResult, SynthesisCampaignCoordinator
    from evolution.domain.enums import SynthesisMode
    from evolution.infra.concurrency.worker import run_synthesis_worker

    mock_sqlite = MagicMock()
    from evolution.application.synthesis_config import SynthesisConfig

    mock_config = SynthesisConfig()
    mock_llm = MagicMock()
    mock_llm.model.name = "mock_model"
    mock_logger = MagicMock()

    mock_engine = MagicMock()
    dispatcher = MagicMock()
    service = SynthesisCampaignCoordinator(
        worker_count=1,
        sqlite_repo=mock_sqlite,
        model_name=mock_llm.model.name,
        logger=mock_logger,
        engine=mock_engine,
        problem_factory=BBOBProblemFactory(),
        dispatcher=dispatcher,
        worker_fn=run_synthesis_worker,
    )
    service_planner = service._build_planner(mock_config)

    # 1. Test run_worker
    from evolution.application import SessionConfig, SingleSynthesisUseCase
    from evolution.domain.enums import PromptStrategy

    mock_problem = MagicMock()
    mock_problem.problem_id = 1
    mock_problem.dim = 2
    dummy_result = SessionResult(
        problem_id=1,
        dim=2,
        mode=SynthesisMode.EXPLICIT,
        noise_std=0.0,
        experiment_id=999,
        best_error=0.05,
    )
    dispatcher.run.return_value = {"test_task_key": dummy_result}
    mock_engine.run.return_value = dummy_result
    mock_task = {
        "key": "test_task_key",
        "problem": mock_problem,
        "experiment_id": 999,
        "config": SessionConfig(iterations=1),
        "engine": mock_engine,
        "prompt_strategy": PromptStrategy.BASELINE,
        "synthesis_mode": SynthesisMode.EXPLICIT,
        "initial_iteration": 0,
    }
    with patch("shared.infra.di.Database") as mock_database:
        # Class registrations capture the real constructor. Supply a usable
        # session-factory substitute instead of patching a removed factory method.
        res = run_synthesis_worker(item=mock_task)
        mock_database.return_value.dispose.assert_called_once()
    assert res is dummy_result
    mock_engine.run.assert_called_once()

    # 2. Test SingleSynthesisUseCase standalone execution
    single_uc = SingleSynthesisUseCase(
        engine=mock_engine, sqlite_repo=mock_sqlite, logger=mock_logger
    )
    res_single = single_uc.execute(
        problem=mock_problem,
        experiment_id=999,
        config=SessionConfig(iterations=1),
        key="standalone_key",
    )
    assert res_single is dummy_result

    # 3. Test run_campaign when no tasks
    with (
        patch.object(service, "_build_planner", return_value=service_planner),
        patch.object(service_planner, "build_tasks", return_value=[]),
    ):
        empty_res = service.run_campaign(**run_parameters(service_planner.config))
        assert empty_res.results == {}
        mock_logger.success.assert_called()

    # 4. Test run_campaign when tasks exist
    mock_item = {
        "key": "test_task_key",
        "problem": mock_problem,
        "experiment_id": 999,
        "config": SessionConfig(iterations=1),
        "engine": mock_engine,
        "initial_iteration": 0,
        "prompt_strategy": PromptStrategy.BASELINE,
        "synthesis_mode": SynthesisMode.EXPLICIT,
    }
    with (
        patch.object(service, "_build_planner", return_value=service_planner),
        patch.object(service_planner, "build_tasks", return_value=[mock_item]),
    ):
        campaign_res = service.run_campaign(**run_parameters(service_planner.config))
        assert campaign_res.results == {"test_task_key": dummy_result}
        dispatcher.run.assert_called_once()


def test_campaign_usecase_audit_matrix_standalone():
    """Verify CampaignAuditor audits coverage for an explicitly selected model."""

    from evolution.application.campaign.audit import CampaignAuditor
    from evolution.application.synthesis_config import SynthesisConfig

    mock_sqlite = MagicMock()
    mock_sqlite.load.return_value = []
    config = SynthesisConfig(
        runs_per_config=2,
        retry_failed_synthesis=True,
        auto_resume=True,
        skip_completed=True,
    )
    mock_logger = MagicMock()

    auditor = CampaignAuditor(
        sqlite_repo=mock_sqlite,
        config=config,
        logger=mock_logger,
        model_name="mock_model_standalone",
    )

    df_matrix, summary = auditor.audit_matrix()
    assert df_matrix.empty
    assert summary["model_name"] == "mock_model_standalone"
    mock_sqlite.load.assert_called_once_with(llm_name="mock_model_standalone")
    mock_logger.audit_summary.assert_called_once()


if __name__ == "__main__":
    test_nb01_noise_pipeline()
    test_nb02_synthesis_pipeline()
    test_nb03_benchmark_pipeline()
    test_nb04_audit_pipeline()
    test_statistical_analysis_pipeline()
    test_custom_minimal_base_logger()
    test_campaign_usecase_run_worker_and_campaign()
    test_campaign_usecase_audit_matrix_standalone()
