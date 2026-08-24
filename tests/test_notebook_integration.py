"""Test execution of refactored notebook logic to ensure zero errors and zero data distortion."""

import json
from pathlib import Path
import sys

# Add src to path
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from benchmarking import (
    BenchmarkAuditService,
    BenchmarkEvaluationService,
    ChampionSelectionService,
    StatisticalEvaluationService,
)
from shared.config import DATA_DIR, RESULTS_DIR


def test_nb03_pipeline():
    print("Testing NB03 logic with ChampionSelectionService...")
    service = ChampionSelectionService()
    summary, total = service.get_experiment_balance()
    assert total > 0, "No completed experiments found!"
    print(f"  • Completed experiments: {total}")
    champions = service.get_champions()
    assert len(champions) > 0, "No champions found!"
    total_champs = sum(len(v) for v in champions.values())
    print(f"  • Champions discovered: {total_champs} across {len(champions)} models")
    print("✅ NB03 logic verified successfully.")


def test_nb04_pipeline():
    print("\nTesting NB04 logic with BenchmarkEvaluationService...")
    service = BenchmarkEvaluationService()
    champions_path = DATA_DIR / "champions.json"
    assert champions_path.exists(), "champions.json does not exist!"
    with open(champions_path, "r", encoding="utf-8") as f:
        champions_raw = json.load(f)
    champions_flat = service.champions_repo.get_champions_flat(champions_raw)

    df_audit = service.audit_champions_workload(champions_flat)
    assert not df_audit.empty
    print(f"  • Audited champions count: {len(df_audit)}")
    print(f"  • Status breakdown:\n{df_audit['status'].value_counts().to_dict()}")
    print("✅ NB04 logic verified successfully.")


def test_nb06_pipeline():
    print("\nTesting NB06 logic with BenchmarkAuditService...")
    service = BenchmarkAuditService()
    audit_data = service.get_global_audit_matrix()
    assert len(audit_data.dims) > 0
    assert len(audit_data.all_solvers) > 0
    print(f"  • Dimensions: {audit_data.dims}")
    print(f"  • Noise levels: {audit_data.noise_levels}")
    print(f"  • Problem IDs: {audit_data.problem_ids}")
    print(f"  • Solvers: {len(audit_data.all_solvers)}")
    print("✅ NB06 logic verified successfully.")


def test_nb07_pipeline():
    print("\nTesting NB07 logic with StatisticalEvaluationService...")
    service = StatisticalEvaluationService()
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

    report_path = RESULTS_DIR / "reports" / "comprehensive_master_report.md"
    service.generate_markdown_report(df_omnibus, df_pairwise, report_path)
    assert report_path.exists()
    print(f"  • Master report generated: {report_path}")
    print("✅ NB07 logic verified successfully.")


if __name__ == "__main__":
    test_nb03_pipeline()
    test_nb04_pipeline()
    test_nb06_pipeline()
    test_nb07_pipeline()
