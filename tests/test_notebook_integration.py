"""Test execution of consolidated 5-notebook pipeline to ensure zero errors and data integrity."""

import json

from benchmarking.application.audit_service import EvaluationAuditService
from benchmarking.application.evaluation_service import EvaluationService
from benchmarking.application.selection_service import ChampionSelectionService
from benchmarking.application.statistical_service import StatisticalEvaluationService
from shared.config import DATA_DIR, RESULTS_DIR


def test_nb01_noise_pipeline():
    """Verify Notebook 01 (01_noise.ipynb: Noise Landscape & Problem Evaluation)."""
    from evolution.domain.services.noise_strategy import HeteroscedasticNoiseStrategy
    from evolution.infra.problems.bbob import BBOBProblem
    p = BBOBProblem(problem_id=1, dim=2, noise_strategy=HeteroscedasticNoiseStrategy(0.05))
    val = p([0.0, 0.0])
    assert isinstance(val, float)
    print("✅ NB01 noise pipeline verified.")


def test_nb02_synthesis_pipeline():
    """Verify Notebook 02 (02_synthesis.ipynb: Evolutionary Synthesis Service & Task Construction)."""
    from evolution.application.synthesis_service import LLaMEASynthesisService
    from evolution.infra.llm.client import LLMClient
    from evolution.infra.logging import SynthesisLogger
    from evolution.infra.storage.synthesis_config.repository import SynthesisConfigRepository
    from shared.database import initialize_sqlite_storage

    # Explicit repository and logger dependency injection
    sqlite_repo = initialize_sqlite_storage()
    config_repo = SynthesisConfigRepository()
    llm = LLMClient("local", skip_validation=True)
    logger = SynthesisLogger(verbose=False)
    service = LLaMEASynthesisService(
        sqlite_repo=sqlite_repo,
        config_repo=config_repo,
        llm_client=llm,
        logger=logger,
    )

    assert service.sqlite_repo is sqlite_repo
    assert service.config_repo is config_repo
    assert service.llm_client is llm
    assert service.logger is logger

    cfg = config_repo.load_config()
    assert "matrix" in cfg
    assert "evolution" in cfg
    assert "problem_targets" in cfg
    assert len(cfg["problem_targets"]) == 5
    assert cfg["problem_ids"] == [1, 8, 11, 15, 21]
    assert cfg["dimensions"] == [2, 3, 5]

    matrix_df, summary = service.audit_matrix()
    assert not matrix_df.empty
    assert "total_conditions" in summary
    assert "problem_targets" in summary

    tasks = service.build_tasks()
    assert len(tasks) > 0

    print(f"✅ NB02 evolutionary synthesis pipeline verified ({len(tasks)} tasks constructed).")


def test_nb03_evaluation_pipeline():
    """Verify Notebook 03 (03_evaluation.ipynb: Champion Selection + Evaluations Audit & Dispatch)."""
    print("Testing NB03 logic with ChampionSelectionService & EvaluationService...")
    from benchmarking.infra.io.trace_repository import IOHTraceReader
    from benchmarking.infra.storage import (
        ChampionsReadRepository,
        SQLiteSynthesisReadRepository,
    )
    from shared.database import create_db_session_factory

    session_factory = create_db_session_factory()
    sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
    champions_repo = ChampionsReadRepository(session_factory)
    trace_repo = IOHTraceReader()

    champ_service = ChampionSelectionService(sqlite_repo=sqlite_repo, champions_repo=champions_repo)
    summary, total = champ_service.get_experiment_balance()
    assert total > 0, "No completed experiments found!"
    print(f"  • Completed experiments: {total}")

    champions = champ_service.get_champions()
    assert len(champions) > 0, "No champions found!"
    total_champs = sum(len(v) for v in champions.values())
    print(f"  • Champions discovered: {total_champs} across {len(champions)} models")

    from benchmarking.infra.io.trace_repository import EvaluationStateRepository
    from benchmarking.infra.logging import EvaluationLogger
    from benchmarking.infra.storage import EvaluationConfigRepository
    state_repo = EvaluationStateRepository()
    config_repo = EvaluationConfigRepository()
    logger = EvaluationLogger()

    eval_service = EvaluationService(
        sqlite_repo=sqlite_repo,
        champions_repo=champions_repo,
        trace_repo=trace_repo,
        state_repo=state_repo,
        config_repo=config_repo,
        logger=logger,
    )
    champions_path = DATA_DIR / "champions.json"
    assert champions_path.exists(), "champions.json does not exist!"
    with open(champions_path, "r", encoding="utf-8") as f:
        champions_raw = json.load(f)
    champions_flat = eval_service.champions_repo.get_champions_flat(champions_raw)
    assert len(champions_flat) > 0

    df_audit = eval_service.audit_champions_workload()
    assert not df_audit.empty
    print(f"  • Audited champions count: {len(df_audit)}")
    print("✅ NB03 benchmark evaluation pipeline verified.")


def test_nb04_audit_pipeline():
    """Verify Notebook 04 (04_audit.ipynb: Experimental Matrix Audit)."""
    print("\nTesting NB04 logic with EvaluationAuditService...")
    from benchmarking.infra.io.trace_repository import IOHTraceReader
    from benchmarking.infra.storage import EvaluationConfigRepository, SQLiteSynthesisReadRepository
    from shared.database import create_db_session_factory

    session_factory = create_db_session_factory()
    sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
    trace_repo = IOHTraceReader()
    config_repo = EvaluationConfigRepository()

    service = EvaluationAuditService(
        sqlite_repo=sqlite_repo,
        trace_repo=trace_repo,
        config_repo=config_repo,
    )
    audit_data = service.get_global_audit_matrix()
    assert len(audit_data.dims) > 0
    assert len(audit_data.all_solvers) > 0
    print(f"  • Dimensions: {audit_data.dims}")
    print(f"  • Noise levels: {audit_data.noise_levels}")
    print(f"  • Problem IDs: {audit_data.problem_ids}")
    print(f"  • Solvers: {len(audit_data.all_solvers)}")
    print("✅ NB04 experimental matrix audit pipeline verified.")


def test_nb05_analysis_pipeline():
    """Verify Notebook 05 (05_analysis.ipynb: Statistical Hypothesis Testing, Reports & Figures)."""
    print("\nTesting NB05 logic with StatisticalEvaluationService...")
    from benchmarking.infra.io.trace_repository import IOHTraceReader
    from benchmarking.infra.storage import SQLiteSynthesisReadRepository
    from shared.database import create_db_session_factory

    session_factory = create_db_session_factory()
    sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
    trace_repo = IOHTraceReader()

    service = StatisticalEvaluationService(sqlite_repo=sqlite_repo, trace_repo=trace_repo)
    df_exp, df_iter = service.get_synthesis_dataframes()
    all_benchmark_data = service.load_all_traces()
    assert len(all_benchmark_data) > 0
    print(f"  • Problem conditions loaded: {len(all_benchmark_data)}")

    df_omnibus = service.run_omnibus_kruskal(all_benchmark_data)
    df_pairwise = service.run_pairwise_fdr(all_benchmark_data, alpha=0.05)
    print(f"  • Omnibus tests: {len(df_omnibus)} rows")
    print(f"  • Pairwise tests (FDR-corrected): {len(df_pairwise)} rows")

    r_val, p_val = service.compute_synthesis_transfer_correlation(df_exp)
    print(f"  • Synthesis transfer correlation: r = {r_val:.3f} (p = {p_val:.3e})")

    # Verify figure computing methods
    solvers = all_benchmark_data.solvers
    p_ids = all_benchmark_data.problem_ids
    dim = all_benchmark_data.dims[0]

    matrix, labels = service.compute_fragility_matrix(all_benchmark_data, dim, solvers, p_ids)
    assert matrix.shape == (len(p_ids), len(solvers))

    c_meds, n_meds, _ = service.compute_validation_medians(all_benchmark_data, dim, p_ids)
    assert len(c_meds) == len(p_ids)

    valid_s, c_rates, n_rates, deltas = service.compute_robustness_profile(all_benchmark_data, dim, solvers, p_ids)
    assert len(valid_s) == len(c_rates) == len(n_rates) == len(deltas)

    report_path = RESULTS_DIR / "reports" / "comprehensive_master_report.md"
    service.generate_markdown_report(df_omnibus, df_pairwise, report_path)
    assert report_path.exists()
    print(f"  • Master report generated: {report_path}")
    print("✅ NB05 statistical analysis & figures pipeline verified.")


def test_synthesis_config_problem_targets_and_fallbacks(tmp_path):
    """Verify Option 3 problem_targets parsing, per-problem dimensions, and legacy fallback."""
    from unittest.mock import MagicMock
    from evolution.application.synthesis_service import LLaMEASynthesisService
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
    assert cfg["problem_targets"] == [
        {"id": 1, "dimensions": [2, 5]},
        {"id": 8, "dimensions": [3]},
    ]
    assert cfg["problem_ids"] == [1, 8]
    assert cfg["dimensions"] == [2, 3, 5]

    mock_sqlite = MagicMock()
    mock_sqlite.load.return_value = []
    mock_llm = MagicMock()
    mock_llm.model.name = "mock_model"
    mock_logger = MagicMock()

    service = LLaMEASynthesisService(
        sqlite_repo=mock_sqlite,
        config_repo=repo,
        llm_client=mock_llm,
        logger=mock_logger,
    )

    tasks = service.build_tasks()
    # Problem 1 has 2D and 5D (2 tasks), Problem 8 has 3D (1 task) -> total 3 tasks
    assert len(tasks) == 3
    task_keys = [t.key for t in tasks]
    assert any("f1_2D" in k for k in task_keys)
    assert any("f1_5D" in k for k in task_keys)
    assert any("f8_3D" in k for k in task_keys)
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
    assert legacy_cfg["problem_targets"] == [
        {"id": 1, "dimensions": [2, 3]},
        {"id": 11, "dimensions": [2, 3]},
    ]
    assert legacy_cfg["problem_ids"] == [1, 11]
    assert legacy_cfg["dimensions"] == [2, 3]


if __name__ == "__main__":
    test_nb01_noise_pipeline()
    test_nb02_synthesis_pipeline()
    test_nb03_evaluation_pipeline()
    test_nb04_audit_pipeline()
    test_nb05_analysis_pipeline()

