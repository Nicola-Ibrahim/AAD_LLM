"""Test execution of consolidated 5-notebook pipeline to ensure zero errors and data integrity."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd

from benchmarking.application.evaluation.audit import EvaluationAuditService
from benchmarking.application.evaluation.run import EvaluationService
from benchmarking.application.select_champions import ChampionSelectionService
from benchmarking.application.analysis import AnalysisData, generate_markdown_report
from shared.config import RESULTS_DIR
from evolution.infra.problems.factory import BBOBProblemFactory
from evolution.infra.execution.candidate_executor import create_candidate_executor
from benchmarking.infra.io.code_reader import FilesystemCodeReader
from benchmarking.infra.solvers.baselines import get_baseline_runner
from benchmarking.infra.io.markdown_report_writer import MarkdownFileWriter
from shared.config import PROJECT_ROOT
from benchmarking.infra.storage.model_registry import configured_model_names
from evolution.infra.concurrency.runner import ProcessPoolRunner
from evolution.infra.concurrency.worker import run_synthesis_worker


def build_evaluation_service(**kwargs):
    project_root = kwargs.pop("project_root", PROJECT_ROOT)
    config_repo = kwargs.pop("config_repo")
    return EvaluationService(
        **kwargs,
        config=config_repo.load_config(),
        problem_factory=BBOBProblemFactory(),
        executor_factory=create_candidate_executor,
        baseline_resolver=get_baseline_runner,
        code_reader=FilesystemCodeReader(project_root),
        model_names=configured_model_names(),
    )


def test_nb00_prompts_pipeline():
    """Verify Notebook 00 (00_prompts.ipynb: Prompts & Diagnostic Feedback Inspection)."""
    from evolution.domain.enums import PromptStrategy, SynthesisMode
    from evolution.application.synthesis.evaluate_candidate import CandidateEvaluationService
    from evolution.domain.services.noise_strategy import (
        HeteroscedasticNoiseStrategy,
        NoNoiseStrategy,
    )
    from evolution.infra.engines.llamea.prompts import (
        FeedbackRenderer,
        META_FEEDBACK_DIVERSITY_INJECTION,
        build_example_prompt,
        build_format_prompt,
        build_task_prompt,
    )
    from evolution.infra.problems.bbob import BBOBProblem

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
    from evolution.domain.services.noise_strategy import HeteroscedasticNoiseStrategy
    from evolution.infra.problems.bbob import BBOBProblem

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
    from evolution.infra.storage.synthesis_config.repository import SynthesisConfigRepository
    from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository
    from shared.infra.database import Database
    from shared.infra.database.tables import Base

    # Exercise the notebook workflow against a fresh schema, not historical data.
    database = Database(f"sqlite:///{tmp_path / 'synthesis.db'}")
    Base.metadata.create_all(database.engine)
    sqlite_repo = SQLiteSynthesisRepository(database.session_factory)
    config_repo = SynthesisConfigRepository()
    llm = LLMClient("local")
    logger = SynthesisLogger(verbose=False)
    engine = LLaMEAEngine(llm_client=llm, code_repo=CodeRepository())

    campaign_usecase = SynthesisCampaignCoordinator(
        sqlite_repo=sqlite_repo,
        config=config_repo.load_config(),
        model_name=llm.model.name,
        logger=logger,
        engine=engine,
        problem_factory=BBOBProblemFactory(),
        dispatcher=ProcessPoolRunner(max_workers=1),
        worker_fn=run_synthesis_worker,
    )

    assert campaign_usecase.planner.sqlite_repo is sqlite_repo
    assert campaign_usecase.config is campaign_usecase.planner.config
    assert campaign_usecase.model_name == llm.model.name
    assert campaign_usecase.logger is logger
    assert isinstance(campaign_usecase.logger, BaseLogger)
    assert hasattr(campaign_usecase.auditor, "audit_matrix")
    assert hasattr(campaign_usecase.planner, "build_tasks")
    assert hasattr(campaign_usecase, "run_campaign")

    cfg = config_repo.load_config()
    assert len(cfg.problem_targets) == 5
    assert cfg.problem_ids == [1, 8, 11, 15, 21]
    assert cfg.dimensions == [2, 3, 5, 10]

    matrix_df, summary = campaign_usecase.auditor.audit_matrix()
    assert not matrix_df.empty
    assert isinstance(matrix_df.index, pd.MultiIndex)
    assert list(matrix_df.index.names) == ["Problem", "Dimension", "Environment", "Strategy"]
    assert "Target Runs" in matrix_df.columns
    assert "Completed" in matrix_df.columns
    assert "Status" in matrix_df.columns
    assert "total_conditions" in summary
    assert "problem_targets" in summary

    tasks = campaign_usecase.planner.build_tasks()
    assert len(tasks) > 0

    print(f"✅ NB02 evolutionary synthesis pipeline verified ({len(tasks)} tasks constructed).")


def test_nb03_evaluation_pipeline():
    """Verify Notebook 03 (03_evaluation.ipynb: Champion Selection + Evaluations Audit & Dispatch)."""
    print("Testing NB03 logic with ChampionSelectionService & EvaluationService...")
    from benchmarking.infra.storage import (
        ChampionsReadRepository,
        SQLiteSynthesisReadRepository,
    )
    from shared.infra.database import Database

    session_factory = Database().session_factory
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

    from benchmarking.infra.io.trace_repository import EvaluationStateRepository
    from benchmarking.infra.logging import EvaluationLogger
    from benchmarking.infra.storage import EvaluationConfigRepository

    state_repo = EvaluationStateRepository()
    config_repo = EvaluationConfigRepository()
    logger = EvaluationLogger()

    eval_service = build_evaluation_service(
        sqlite_repo=sqlite_repo,
        champions_repo=champions_repo,
        state_repo=state_repo,
        config_repo=config_repo,
        logger=logger,
    )
    champions_path = RESULTS_DIR / "benchmark" / "champions.json"
    champ_service.export_champions(champions_path)
    assert champions_path.exists(), "champions.json does not exist!"
    with open(champions_path, "r", encoding="utf-8") as f:
        champions_raw = json.load(f)
    champions_flat = eval_service.champion_selection.flatten_champions(champions_raw)
    assert len(champions_flat) > 0

    df_audit = eval_service.workload.audit_champions_workload()
    assert not df_audit.empty
    print(f"  • Audited champions count: {len(df_audit)}")
    print("✅ NB03 benchmark evaluation pipeline verified.")


def test_nb03_import_order_isolation():
    """Verify Notebook 03 imports succeed in a clean subprocess where infra is loaded before application."""
    import subprocess
    import sys

    cmd = [
        sys.executable,
        "-c",
        "import sys\n"
        "sys.path.insert(0, 'src')\n"
        "from benchmarking.infra.io.trace_repository import EvaluationStateRepository, IOHTraceReader\n"
        "from benchmarking.infra.storage import (\n"
        "    EvaluationConfigRepository,\n"
        "    ChampionsReadRepository,\n"
        "    SQLiteSynthesisReadRepository,\n"
        ")\n"
        "from benchmarking.application.select_champions import ChampionSelectionService\n"
        "from benchmarking.application.evaluation.run import EvaluationService\n"
        "from benchmarking.infra.logging import EvaluationLogger\n"
        "repo = EvaluationConfigRepository()\n"
        "cfg = repo.load_config()\n"
        "assert cfg.target_eval_runs > 0\n"
        "print('NB03 import order verified.')\n",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "NB03 import order verified." in result.stdout


def test_nb04_audit_pipeline():
    """Verify Notebook 04 (04_audit.ipynb: Experimental Matrix Audit)."""
    print("\nTesting NB04 logic with EvaluationAuditService...")
    from benchmarking.infra.io.trace_repository import IOHTraceReader
    from benchmarking.infra.storage import EvaluationConfigRepository, SQLiteSynthesisReadRepository
    from shared.infra.database import Database

    session_factory = Database().session_factory
    sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
    trace_repo = IOHTraceReader()
    config_repo = EvaluationConfigRepository()

    service = EvaluationAuditService(
        sqlite_repo=sqlite_repo,
        trace_repo=trace_repo,
        config=config_repo.load_config(),
        model_names=configured_model_names(),
    )
    audit_data = service.get_global_audit_matrix()
    assert hasattr(audit_data, "dims")
    assert hasattr(audit_data, "all_solvers")
    assert hasattr(audit_data, "coverage_summary")
    if len(audit_data.dims) > 0:
        assert len(audit_data.all_solvers) > 0
        print(f"  • Dimensions: {audit_data.dims}")
        print(f"  • Noise levels: {audit_data.noise_levels}")
        print(f"  • Problem IDs: {audit_data.problem_ids}")
        print(f"  • Solvers: {len(audit_data.all_solvers)}")
    else:
        print(
            "  • Database in fresh/running state: audit matrix initialized with default empty grid."
        )
    print("✅ NB04 experimental matrix audit pipeline verified.")


def test_nb05_analysis_pipeline(tmp_path):
    """Verify Notebook 05 (05_analysis.ipynb: Statistical Hypothesis Testing, Reports & Figures)."""
    print("\nTesting NB05 logic with AnalysisData...")
    from benchmarking.infra.io.trace_repository import IOHTraceReader
    from benchmarking.infra.storage import SQLiteSynthesisReadRepository
    from shared.infra.database import Database

    session_factory = Database().session_factory
    sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
    trace_repo = IOHTraceReader()

    service = AnalysisData(
        sqlite_repo=sqlite_repo,
        trace_repo=trace_repo,
        model_names=configured_model_names(),
    )
    df_exp, df_iter = service.get_synthesis_dataframes()
    all_benchmark_data = service.load_evaluation_traces()
    assert len(all_benchmark_data) > 0
    print(f"  • Problem conditions loaded: {len(all_benchmark_data)}")

    df_omnibus = service.hypothesis_engine.run_omnibus_kruskal(all_benchmark_data)
    df_pairwise = service.hypothesis_engine.run_pairwise_fdr(all_benchmark_data, alpha=0.05)
    print(f"  • Omnibus tests: {len(df_omnibus)} rows")
    print(f"  • Pairwise tests (FDR-corrected): {len(df_pairwise)} rows")

    r_val, p_val = service.hypothesis_engine.compute_synthesis_transfer_correlation(df_exp)
    print(f"  • Synthesis transfer correlation: r = {r_val:.3f} (p = {p_val:.3e})")

    # Verify figure computing methods
    solvers = all_benchmark_data.solvers
    p_ids = all_benchmark_data.problem_ids
    dim = all_benchmark_data.dims[0]

    matrix, labels = service.performance_engine.compute_fragility_matrix(
        all_benchmark_data, dim, solvers, p_ids
    )
    assert matrix.shape == (len(p_ids), len(solvers))

    c_meds, n_meds, _ = service.performance_engine.compute_validation_medians(
        all_benchmark_data, dim, p_ids
    )
    assert len(c_meds) == len(p_ids)

    valid_s, c_rates, n_rates, deltas = service.performance_engine.compute_robustness_profile(
        all_benchmark_data, dim, solvers, p_ids
    )
    assert len(valid_s) == len(c_rates) == len(n_rates) == len(deltas)

    report_path = tmp_path / "comprehensive_master_report.md"
    generate_markdown_report(df_omnibus, df_pairwise, report_path, writer=MarkdownFileWriter())
    assert report_path.exists()
    print(f"  • Master report generated: {report_path}")
    print("✅ NB05 statistical analysis & figures pipeline verified.")


def test_synthesis_config_problem_targets_and_fallbacks(tmp_path):
    """Verify Option 3 problem_targets parsing, per-problem dimensions, and legacy fallback."""
    from evolution.application import SynthesisCampaignCoordinator
    from evolution.application.synthesis_config import ProblemTarget
    from evolution.infra.engines.llamea import LLaMEAEngine
    from evolution.infra.storage.code.repository import CodeRepository
    from evolution.infra.storage.synthesis_config import SynthesisConfigRepository

    # 1. Custom per-problem dimensions
    custom_toml = tmp_path / "custom.toml"
    custom_toml.write_text("""
[matrix]
problem_targets = [
  { id = 1, dimensions = [2, 5] },
  { id = 8, dimensions = [3] },
]
noise_conditions = [
  { std = 0.0, model = "none" },
]
prompt_strategies = ["baseline"]

[evolution]
iterations = 1
budget = 1000
runs_per_config = 1
""")
    repo = SynthesisConfigRepository(config_path=custom_toml)
    cfg = repo.load_config()
    assert cfg.problem_targets == [
        ProblemTarget(id=1, dimensions=[2, 5]),
        ProblemTarget(id=8, dimensions=[3]),
    ]
    assert cfg.problem_ids == [1, 8]
    assert cfg.dimensions == [2, 3, 5]

    mock_sqlite = MagicMock()
    mock_sqlite.load.return_value = []
    mock_llm = MagicMock()
    mock_llm.model.name = "mock_model"
    mock_logger = MagicMock()
    engine = LLaMEAEngine(llm_client=mock_llm, code_repo=CodeRepository())
    service = SynthesisCampaignCoordinator(
        sqlite_repo=mock_sqlite,
        config=repo.load_config(),
        model_name=mock_llm.model.name,
        logger=mock_logger,
        engine=engine,
        problem_factory=BBOBProblemFactory(),
        dispatcher=ProcessPoolRunner(max_workers=1),
        worker_fn=run_synthesis_worker,
    )

    tasks = service.planner.build_tasks()
    # Problem 1 has 2D and 5D (2x2=4 tasks), Problem 8 has 3D (1x2=2 tasks) -> total 6 tasks (both explicit and implicit)
    assert len(tasks) == 6
    task_keys = [t["key"] for t in tasks]
    assert any("f1_2D_explicit" in k for k in task_keys)
    assert any("f1_2D_implicit" in k for k in task_keys)
    assert any("f1_5D_explicit" in k for k in task_keys)
    assert any("f8_3D_explicit" in k for k in task_keys)
    assert not any("f8_2D" in k for k in task_keys)
    assert not any("f8_5D" in k for k in task_keys)

    # 2. Legacy fallback
    legacy_toml = tmp_path / "legacy.toml"
    legacy_toml.write_text("""
[matrix]
problem_ids = [1, 11]
dimensions = [2, 3]
noise_stds = [0.0]
prompt_strategies = ["baseline"]
""")
    legacy_repo = SynthesisConfigRepository(config_path=legacy_toml)
    legacy_cfg = legacy_repo.load_config()
    assert legacy_cfg.problem_targets == [
        ProblemTarget(id=1, dimensions=[2, 3]),
        ProblemTarget(id=11, dimensions=[2, 3]),
    ]
    assert legacy_cfg.problem_ids == [1, 11]
    assert legacy_cfg.dimensions == [2, 3]

    # 3. Multi-mode (explicit, implicit)
    multimode_toml = tmp_path / "multimode.toml"
    multimode_toml.write_text("""
[matrix]
problem_targets = [
  { id = 1, dimensions = [2] },
]
noise_conditions = [
  { std = 0.0, noise_model = "none" },
  { std = 0.05, noise_model = "heteroscedastic" },
]
synthesis_modes = ["explicit", "implicit"]
prompt_strategies = ["baseline"]

[evolution]
iterations = 1
budget = 1000
runs_per_config = 1
""")
    mm_repo = SynthesisConfigRepository(config_path=multimode_toml)
    mm_cfg = mm_repo.load_config()
    assert mm_cfg.synthesis_mode_names == ["explicit", "implicit"]

    mm_engine = LLaMEAEngine(llm_client=mock_llm, code_repo=CodeRepository())
    mm_service = SynthesisCampaignCoordinator(
        sqlite_repo=mock_sqlite,
        config=mm_repo.load_config(),
        model_name=mock_llm.model.name,
        logger=mock_logger,
        engine=mm_engine,
        problem_factory=BBOBProblemFactory(),
        dispatcher=ProcessPoolRunner(max_workers=1),
        worker_fn=run_synthesis_worker,
    )
    mm_tasks = mm_service.planner.build_tasks()
    # 1 problem, 1 dim: 2 noise conditions x 2 modes -> total 4 tasks
    assert len(mm_tasks) == 4
    mm_keys = [t["key"] for t in mm_tasks]
    assert any("explicit_std_0.0" in k for k in mm_keys)
    assert any("explicit_std_0.05" in k for k in mm_keys)
    assert any("implicit_std_0.0" in k for k in mm_keys)
    assert any("implicit_std_0.05" in k for k in mm_keys)

    # 4. Structured list of dictionaries for synthesis_modes with custom strategies
    dict_modes_toml = tmp_path / "dict_modes.toml"
    dict_modes_toml.write_text("""
[matrix]
problem_targets = [
  { id = 1, dimensions = [2] },
]
noise_conditions = [
  { std = 0.05, noise_model = "heteroscedastic" },
]
synthesis_modes = [
  { mode = "explicit", strategies = ["baseline", "thinking"] },
  { mode = "implicit", strategies = ["guided"] },
]

[evolution]
iterations = 1
budget = 1000
runs_per_config = 1
""")
    dm_repo = SynthesisConfigRepository(config_path=dict_modes_toml)
    dm_cfg = dm_repo.load_config()
    assert len(dm_cfg.synthesis_modes) == 2
    assert dm_cfg.synthesis_modes[0].mode.value == "explicit"
    assert [strategy.value for strategy in dm_cfg.synthesis_modes[0].strategies] == [
        "baseline",
        "thinking",
    ]
    assert dm_cfg.synthesis_modes[1].mode.value == "implicit"
    assert [strategy.value for strategy in dm_cfg.synthesis_modes[1].strategies] == ["guided"]
    assert [strategy.value for strategy in dm_cfg.prompt_strategies] == [
        "baseline",
        "guided",
        "thinking",
    ]

    dm_engine = LLaMEAEngine(llm_client=mock_llm, code_repo=CodeRepository())
    dm_service = SynthesisCampaignCoordinator(
        sqlite_repo=mock_sqlite,
        config=dm_repo.load_config(),
        model_name=mock_llm.model.name,
        logger=mock_logger,
        engine=dm_engine,
        problem_factory=BBOBProblemFactory(),
        dispatcher=ProcessPoolRunner(max_workers=1),
        worker_fn=run_synthesis_worker,
    )
    dm_tasks = dm_service.planner.build_tasks()
    # 1 problem, 1 dim, std=0.05:
    # explicit has 2 strategies (baseline, thinking) -> 2 tasks
    # implicit has 1 strategy (guided) -> 1 task
    # total = 3 tasks
    assert len(dm_tasks) == 3
    dm_keys = [t["key"] for t in dm_tasks]
    assert any("explicit_std_0.05_baseline" in k for k in dm_keys)
    assert any("explicit_std_0.05_thinking" in k for k in dm_keys)
    assert any("implicit_std_0.05_guided" in k for k in dm_keys)
    assert not any("implicit_std_0.05_baseline" in k for k in dm_keys)


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
    from unittest.mock import MagicMock, patch
    from evolution.application import SessionResult, SynthesisCampaignCoordinator
    from evolution.domain.enums import SynthesisMode
    from evolution.infra.concurrency.worker import run_synthesis_worker

    mock_sqlite = MagicMock()
    mock_config = MagicMock()
    mock_config.load_config.return_value = MagicMock(
        budget=1000,
        timeout_seconds=60.0,
        iterations=5,
        runs_per_config=1,
        num_processes=2,
        auto_resume=False,
        skip_completed=True,
        retry_failed_synthesis=False,
        only_incomplete=False,
        target_exp_ids=[],
        problem_targets=[],
        problems=[1],
        dimensions=[2],
        noise_conditions=[],
        noise_stds=[0.0],
        noise_model=MagicMock(),
        synthesis_modes=[],
        mode_enums=[SynthesisMode.EXPLICIT],
        synthesis_mode=SynthesisMode.EXPLICIT,
        prompt_strategies=[],
        matrix_conditions=[],
    )
    mock_llm = MagicMock()
    mock_llm.model.name = "mock_model"
    mock_logger = MagicMock()

    mock_engine = MagicMock()
    dispatcher = MagicMock()
    service = SynthesisCampaignCoordinator(
        sqlite_repo=mock_sqlite,
        config=mock_config,
        model_name=mock_llm.model.name,
        logger=mock_logger,
        engine=mock_engine,
        problem_factory=BBOBProblemFactory(),
        dispatcher=dispatcher,
        worker_fn=run_synthesis_worker,
    )

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
    with patch("shared.infra.database.Database") as mock_database:
        mock_database.return_value.session_factory = object()
        with patch(
            "evolution.infra.storage.synthesis.repository.SQLiteSynthesisRepository",
            return_value=mock_sqlite,
        ):
            res = run_synthesis_worker(item=mock_task)
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
    with patch.object(service.planner, "build_tasks", return_value=[]):
        empty_res = service.run_campaign()
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
    with patch.object(service.planner, "build_tasks", return_value=[mock_item]):
        campaign_res = service.run_campaign()
        assert campaign_res.results == {"test_task_key": dummy_result}
        dispatcher.run.assert_called_once()


def test_campaign_usecase_audit_matrix_standalone():
    """Verify CampaignAuditor audits coverage for an explicitly selected model."""
    from unittest.mock import MagicMock
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
    test_nb03_evaluation_pipeline()
    test_nb04_audit_pipeline()
    test_nb05_analysis_pipeline()
    test_custom_minimal_base_logger()
    test_campaign_usecase_run_worker_and_campaign()
    test_campaign_usecase_audit_matrix_standalone()
