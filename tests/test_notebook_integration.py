"""Test execution of consolidated 5-notebook pipeline to ensure zero errors and data integrity."""

import json
from pathlib import Path
import sys

# Add src to path
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from benchmarking.application.audit_service import BenchmarkAuditService
from benchmarking.application.evaluation_service import BenchmarkEvaluationService
from benchmarking.application.selection_service import ChampionSelectionService
from benchmarking.application.statistical_service import StatisticalEvaluationService
from shared.config import DATA_DIR, RESULTS_DIR


def test_nb01_noise_landscapes():
    """Verify Notebook 01 data pipeline."""
    from evolution.infra.problems.bbob import BBOBProblem
    from evolution.domain.services.noise_strategy import HeteroscedasticNoiseStrategy
    p = BBOBProblem(problem_id=1, dim=2, noise_strategy=HeteroscedasticNoiseStrategy(0.05))
    val = p([0.0, 0.0])
    assert isinstance(val, float)
    print("✅ NB01 noise landscape pipeline verified.")


def test_nb02_evolutionary_synthesis_pipeline():
    """Verify Notebook 02 (Evolutionary Synthesis Service & Task Construction with DI)."""
    from evolution.application.experiment_service import EvolutionExperimentService
    from evolution.infra.llm.client import LLMClient
    from evolution.infra.storage.campaigns.repository import ExperimentConfigRepository
    from shared.database import initialize_sqlite_storage

    # Explicit repository dependency injection
    sqlite_repo = initialize_sqlite_storage()
    config_repo = ExperimentConfigRepository()
    llm = LLMClient("local", skip_validation=True)
    service = EvolutionExperimentService(
        sqlite_repo=sqlite_repo,
        config_repo=config_repo,
        llm_client=llm,
    )

    assert service.sqlite_repo is sqlite_repo
    assert service.config_repo is config_repo
    assert service.llm_client is llm

    cfg = config_repo.load_config()
    assert "matrix" in cfg
    assert "budget" in cfg

    matrix_df, summary = service.audit_campaign()
    assert not matrix_df.empty
    assert "total_conditions" in summary

    tasks = service.build_tasks()
    assert len(tasks) > 0

    print(f"✅ NB02 evolutionary synthesis pipeline verified ({len(tasks)} tasks constructed).")


def test_nb03_benchmark_evaluations_pipeline():
    """Verify Notebook 03 (Champion Selection + Evaluations Audit & Dispatch)."""
    print("Testing NB03 logic with ChampionSelectionService & BenchmarkEvaluationService...")
    from benchmarking.infra.io.trace_repository import IOHTraceReader
    from benchmarking.infra.storage import (
        ChampionsReadRepository,
        SQLiteBenchmarkReadRepository,
    )
    from shared.database import create_db_session_factory

    session_factory = create_db_session_factory()
    sqlite_repo = SQLiteBenchmarkReadRepository(session_factory)
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

    eval_service = BenchmarkEvaluationService(
        sqlite_repo=sqlite_repo,
        champions_repo=champions_repo,
        trace_repo=trace_repo,
    )
    champions_path = DATA_DIR / "champions.json"
    assert champions_path.exists(), "champions.json does not exist!"
    with open(champions_path, "r", encoding="utf-8") as f:
        champions_raw = json.load(f)
    champions_flat = eval_service.champions_repo.get_champions_flat(champions_raw)

    df_audit = eval_service.audit_champions_workload(champions_flat)
    assert not df_audit.empty
    print(f"  • Audited champions count: {len(df_audit)}")
    print("✅ NB03 benchmark evaluation pipeline verified.")


def test_nb04_experimental_matrix_audit_pipeline():
    """Verify Notebook 04 (Experimental Matrix Audit)."""
    print("\nTesting NB04 logic with BenchmarkAuditService...")
    from benchmarking.infra.io.trace_repository import IOHTraceReader
    from benchmarking.infra.storage import SQLiteBenchmarkReadRepository
    from shared.database import create_db_session_factory

    session_factory = create_db_session_factory()
    sqlite_repo = SQLiteBenchmarkReadRepository(session_factory)
    trace_repo = IOHTraceReader()

    service = BenchmarkAuditService(sqlite_repo=sqlite_repo, trace_repo=trace_repo)
    audit_data = service.get_global_audit_matrix()
    assert len(audit_data.dims) > 0
    assert len(audit_data.all_solvers) > 0
    print(f"  • Dimensions: {audit_data.dims}")
    print(f"  • Noise levels: {audit_data.noise_levels}")
    print(f"  • Problem IDs: {audit_data.problem_ids}")
    print(f"  • Solvers: {len(audit_data.all_solvers)}")
    print("✅ NB04 experimental matrix audit pipeline verified.")


def test_nb05_statistical_analysis_and_figures_pipeline():
    """Verify Notebook 05 (Statistical Hypothesis Testing, Reports & Figure Data)."""
    print("\nTesting NB05 logic with StatisticalEvaluationService...")
    from benchmarking.infra.io.trace_repository import IOHTraceReader
    from benchmarking.infra.storage import SQLiteBenchmarkReadRepository
    from shared.database import create_db_session_factory

    session_factory = create_db_session_factory()
    sqlite_repo = SQLiteBenchmarkReadRepository(session_factory)
    trace_repo = IOHTraceReader()

    service = StatisticalEvaluationService(sqlite_repo=sqlite_repo, trace_repo=trace_repo)
    df_exp, df_iter = service.get_synthesis_dataframes()
    all_benchmark_data = service.load_evaluation_traces()
    assert len(all_benchmark_data) > 0
    print(f"  • Problem conditions loaded: {len(all_benchmark_data)}")

    df_omnibus = service.run_omnibus_kruskal(all_benchmark_data)
    df_pairwise = service.run_pairwise_fdr(all_benchmark_data, alpha=0.05)
    print(f"  • Omnibus tests: {len(df_omnibus)} rows")
    print(f"  • Pairwise tests (FDR-corrected): {len(df_pairwise)} rows")

    r_val, p_val = service.compute_synthesis_transfer_correlation(df_exp)
    print(f"  • Synthesis transfer correlation: r = {r_val:.3f} (p = {p_val:.3e})")

    # Verify figure computing methods
    solvers = sorted(list(set(s for cond in all_benchmark_data.values() for s in cond.keys())))
    p_ids = sorted(list(set(k[2] for k in all_benchmark_data.keys())))
    dim = list(all_benchmark_data.keys())[0][0]

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


if __name__ == "__main__":
    test_nb01_noise_landscapes()
    test_nb03_benchmark_evaluations_pipeline()
    test_nb04_experimental_matrix_audit_pipeline()
    test_nb05_statistical_analysis_and_figures_pipeline()
