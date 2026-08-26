"""Unit and integration tests for analytics services, domain resolvers, and IOH parsers."""

import numpy as np
import pandas as pd
import pytest

from benchmarking.application.audit_service import BenchmarkAuditService
from benchmarking.application.selection_service import ChampionSelectionService
from benchmarking.application.statistical_service import (
    StatisticalEvaluationService,
    generate_markdown_report,
)
from benchmarking.domain.resolvers import (
    format_db_solver_name,
    get_clean_model_label,
    get_model_slug,
    resolve_folder_solver_name,
)
from benchmarking.domain.statistics import StatisticalEngine
from benchmarking.domain.taxonomy import (
    BBOB_CLASSES,
    BBOB_CLASSES_ORDER,
    BBOB_METADATA,
    BBOB_NAMES,
    get_bbob_class,
    get_bbob_name,
)
from benchmarking.infra.io.trace_repository import IOHTraceReader
from benchmarking.infra.storage.champions_repository import ChampionsReadRepository
from benchmarking.infra.storage.sqlite_repository import SQLiteBenchmarkReadRepository
from shared.config import DATA_DIR, RESULTS_DIR
from shared.database import create_db_session_factory


class TestDomainTaxonomy:
    def test_all_24_bbob_functions_present(self):
        assert len(BBOB_METADATA) == 24
        assert len(BBOB_NAMES) == 24
        assert len(BBOB_CLASSES) == 24

        assert get_bbob_name(1) == "Sphere (f1)"
        assert get_bbob_class(1) == "Separable"
        assert get_bbob_name(8) == "Rosenbrock (f8)"
        assert get_bbob_class(8) == "Low Conditioning"
        assert get_bbob_name(11) == "Discus (f11)"
        assert get_bbob_class(11) == "High Conditioning"
        assert get_bbob_name(15) == "Rastrigin Multi-Modal (f15)"
        assert get_bbob_class(15) == "Multi-Modal (Global)"
        assert get_bbob_name(21) == "Gallagher 101 Peaks (f21)"
        assert get_bbob_class(21) == "Multi-Modal (Weak)"

    def test_landscape_classes_order(self):
        assert len(BBOB_CLASSES_ORDER) == 5
        assert "Separable" in BBOB_CLASSES_ORDER


class TestDomainResolvers:
    def test_clean_model_labels_dynamic(self):
        assert get_clean_model_label("qwen2.5-coder-14b-instruct-q4_k_m.gguf") == "LLaMEA-14B"
        assert get_clean_model_label("qwen2.5-coder-7b-instruct-q4_k_m.gguf") == "LLaMEA-7B"
        assert get_clean_model_label("deepseek-r1-distill-qwen-70b.gguf") == "LLaMEA-70B"
        assert get_clean_model_label("meta-llama-3-8b-instruct") == "LLaMEA-8B"

    def test_format_db_solver_name(self):
        assert (
            format_db_solver_name("qwen2.5-coder-14b-instruct-q4_k_m.gguf", "baseline")
            == "LLaMEA-14B / baseline"
        )
        assert (
            format_db_solver_name("qwen2.5-coder-70b-instruct.gguf", "thinking")
            == "LLaMEA-70B / thinking"
        )

    def test_get_model_slug(self):
        assert get_model_slug("qwen2.5-coder-14b-instruct-q4_k_m.gguf") == "qwen_14b"
        assert get_model_slug("qwen2.5-coder-7b-instruct-q4_k_m.gguf") == "qwen_7b"
        assert get_model_slug("llama-3-8b-instruct") == "llama_8b"

    def test_resolve_folder_solver_name(self):
        # Classical
        assert resolve_folder_solver_name("cmaes") == "CMA-ES"
        assert resolve_folder_solver_name("cma_es") == "CMA-ES"
        assert resolve_folder_solver_name("cmaes-1") == "CMA-ES"
        assert resolve_folder_solver_name("de") == "DE"
        assert resolve_folder_solver_name("de_1") == "DE"
        assert resolve_folder_solver_name("pso") == "PSO"

        # LLM structured folders
        assert resolve_folder_solver_name("qwen_14b_baseline") == "LLaMEA-14B / baseline"
        assert resolve_folder_solver_name("qwen_7b_guided") == "LLaMEA-7B / guided"
        assert resolve_folder_solver_name("qwen_70b_thinking") == "LLaMEA-70B / thinking"


class TestStatisticalEngine:
    @pytest.fixture
    def engine(self):
        return StatisticalEngine()

    def test_vargha_delaney_a12(self, engine):
        s1 = [1.0, 2.0, 3.0]
        s2 = [4.0, 5.0, 6.0]
        a12, mag = engine.vargha_delaney_a12(s1, s2)
        assert a12 == 1.0  # s1 has all values smaller than s2
        assert mag == "large"

        # Identical samples
        a12_eq, mag_eq = engine.vargha_delaney_a12(s1, s1)
        assert a12_eq == 0.5
        assert mag_eq == "negligible"

    def test_omnibus_and_pairwise_fdr_tests(self, engine):
        # Synthetic benchmark dataset
        bench_data = {
            (2, 0.0, 1): {
                "CMA-ES": [(np.array([1, 10]), np.array([10.0, 0.1])) for _ in range(5)],
                "DE": [(np.array([1, 10]), np.array([10.0, 0.5])) for _ in range(5)],
                "LLaMEA-14B / baseline": [(np.array([1, 10]), np.array([10.0, 0.01])) for _ in range(5)],
            }
        }

        df_omni = engine.run_omnibus_kruskal(bench_data)
        assert not df_omni.empty
        assert len(df_omni) == 1
        assert df_omni.iloc[0]["Problem ID"] == 1
        assert df_omni.iloc[0]["Solvers Count"] == 3

        df_pair = engine.run_pairwise_fdr(bench_data)
        assert not df_pair.empty
        assert len(df_pair) == 3  # (CMA vs DE, CMA vs LLM, DE vs LLM)
        assert "p-adjusted" in df_pair.columns
        assert "Outcome" in df_pair.columns

    def test_compute_convergence_iqr(self, engine):
        runs = [
            (np.array([1, 5, 10]), np.array([100.0, 50.0, 1.0])),
            (np.array([1, 5, 10]), np.array([100.0, 40.0, 2.0])),
            (np.array([1, 5, 10]), np.array([100.0, 60.0, 0.5])),
        ]
        eval_grid, med, q25, q75 = engine.compute_convergence_iqr(runs, n_points=10)
        assert len(eval_grid) == 10
        assert len(med) == 10
        assert np.all(med >= q25)
        assert np.all(q75 >= med)


class TestApplicationServicesIntegration:
    def test_selection_service(self):
        session_factory = create_db_session_factory()
        sqlite_repo = SQLiteBenchmarkReadRepository(session_factory)
        champions_repo = ChampionsReadRepository(session_factory)
        service = ChampionSelectionService(sqlite_repo=sqlite_repo, champions_repo=champions_repo)
        summary, count = service.get_experiment_balance()
        if (DATA_DIR / "db.sqlite3").exists():
            assert isinstance(summary, pd.DataFrame)
            assert count >= 0

    def test_audit_service(self):
        session_factory = create_db_session_factory()
        sqlite_repo = SQLiteBenchmarkReadRepository(session_factory)
        service = BenchmarkAuditService(sqlite_repo=sqlite_repo, trace_repo=IOHTraceReader(RESULTS_DIR / "evaluations" / "traces"))
        if (DATA_DIR / "db.sqlite3").exists():
            matrix, summary = service.get_audit_matrix()
            assert isinstance(matrix, pd.DataFrame)
            assert isinstance(summary, dict)
            assert "coverage_pct" in summary

    def test_statistical_service(self):
        session_factory = create_db_session_factory()
        sqlite_repo = SQLiteBenchmarkReadRepository(session_factory)
        trace_repo = IOHTraceReader(RESULTS_DIR / "evaluations" / "traces")
        service = StatisticalEvaluationService(sqlite_repo=sqlite_repo, trace_repo=trace_repo)
        if (DATA_DIR / "db.sqlite3").exists():
            df_exp, df_iter = service.get_synthesis_dataframes()
            assert isinstance(df_exp, pd.DataFrame)
            assert isinstance(df_iter, pd.DataFrame)
            traces = service.load_evaluation_traces()
            assert isinstance(traces, dict)


class TestConcreteInfraRepositories:
    def test_sqlite_benchmark_read_repository(self):
        session_factory = create_db_session_factory()
        repo = SQLiteBenchmarkReadRepository(session_factory)
        if (DATA_DIR / "db.sqlite3").exists():
            df, count = repo.get_experiment_balance()
            assert isinstance(df, pd.DataFrame)
            conditions = repo.get_target_conditions()
            assert isinstance(conditions, list)

    def test_champions_read_repository(self):
        session_factory = create_db_session_factory()
        repo = ChampionsReadRepository(session_factory)
        if (DATA_DIR / "db.sqlite3").exists():
            champs = repo.extract_champions()
            assert isinstance(champs, dict)
            flat = repo.get_champions_flat(champs)
            assert isinstance(flat, dict)

    def test_trace_reader(self):
        repo = IOHTraceReader(RESULTS_DIR / "evaluations" / "traces")
        assert hasattr(repo, "load_evaluation_traces")
        assert hasattr(repo, "get_run_count")
        assert hasattr(repo, "parse_dat_file")


class TestMarkdownReporting:
    def test_generate_markdown_report_empty(self):
        report = generate_markdown_report()
        assert "Comprehensive Empirical Evaluation" in report
        assert "Overview & Experimental Protocol" in report

    def test_generate_markdown_report_with_data(self, tmp_path):
        df_omnibus = pd.DataFrame([
            {"Condition": "3D_std0.0_f1", "Significant": "Yes", "p-value": 0.001}
        ])
        df_pairwise = pd.DataFrame([
            {"Comparison": "A vs B", "p-value": 0.01, "A12": 0.85}
        ])
        out_file = tmp_path / "test_report.md"
        report = generate_markdown_report(df_omnibus=df_omnibus, df_pairwise=df_pairwise, output_path=out_file)
        assert out_file.exists()
        assert "Omnibus Results Table" in report
        assert "Pairwise Statistical Comparisons" in report
        assert "3D_std0.0_f1" in report


