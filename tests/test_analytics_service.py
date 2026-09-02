"""Unit and integration tests for analytics services, domain resolvers, and IOH parsers."""

import numpy as np
import pandas as pd
import pytest

from benchmarking.application.audit_service import AuditCoverageSummary, EvaluationAuditService
from benchmarking.application.selection_service import ChampionSelectionService
from benchmarking.application.statistical_service import (
    StatisticalEvaluationService,
    generate_markdown_report,
)
from benchmarking.domain.services.resolvers import (
    format_db_solver_name,
    get_clean_model_label,
    get_model_slug,
    resolve_folder_solver_name,
)
from benchmarking.domain.services.ecdf import EcdfConvergenceEngine
from benchmarking.domain.services.hypothesis import HypothesisTestingEngine
from benchmarking.domain.services.performance import PerformanceMetricsEngine
from benchmarking.domain.enums import (
    BBOB_CLASSES_ORDER,
    BBOBFunction,
)
from benchmarking.domain.vos import EvaluationCondition, EvaluationDataset, RunTrace
from benchmarking.infra.io.trace_repository import IOHTraceReader
from benchmarking.infra.storage.champions_repository import ChampionsReadRepository
from benchmarking.infra.storage.config_repository import EvaluationConfigRepository
from benchmarking.infra.storage.sqlite_repository import SQLiteSynthesisReadRepository
from shared.config import DATA_DIR, RESULTS_DIR
from shared.database import create_db_session_factory


class TestDomainTaxonomy:
    def test_all_24_bbob_functions_present(self):
        assert len(BBOBFunction) == 24

        assert BBOBFunction.get_name(1) == "Sphere (f1)"
        assert BBOBFunction.get_class(1) == "Separable"
        assert BBOBFunction.get_name(8) == "Rosenbrock (f8)"
        assert BBOBFunction.get_class(8) == "Low Conditioning"
        assert BBOBFunction.get_name(11) == "Discus (f11)"
        assert BBOBFunction.get_class(11) == "High Conditioning"
        assert BBOBFunction.get_name(15) == "Rastrigin Multi-Modal (f15)"
        assert BBOBFunction.get_class(15) == "Multi-Modal (Global)"
        assert BBOBFunction.get_name(21) == "Gallagher 101 Peaks (f21)"
        assert BBOBFunction.get_class(21) == "Multi-Modal (Weak)"

    def test_landscape_classes_order(self):
        assert len(BBOB_CLASSES_ORDER) == 5
        assert "Separable" in BBOB_CLASSES_ORDER


class TestDomainResolvers:
    def test_clean_model_labels_dynamic(self):
        assert get_clean_model_label("qwen2.5-coder-14b-instruct-q4_k_m.gguf") == "Qwen2.5-Coder-14B"
        assert get_clean_model_label("qwen2.5-coder-14b-instruct-q4_k_m") == "Qwen2.5-Coder-14B"
        assert get_clean_model_label("qwen2.5-coder-7b-instruct-q4_k_m.gguf") == "Qwen2.5-Coder-7B"
        assert get_clean_model_label("deepseek-r1-distill-qwen-70b.gguf") == "DeepSeek-70B"
        assert get_clean_model_label("meta-llama-3-8b-instruct") == "Llama-8B"
        assert get_clean_model_label("Meta-Llama-3.1-8B-Instruct.Q4_K_M.gguf") == "Llama-8B"
        # Dynamic fallback for unregistered models without hardcoding
        assert get_clean_model_label("mistral-7b-instruct") == "Mistral-7B"

    def test_format_db_solver_name(self):
        assert (
            format_db_solver_name("qwen2.5-coder-14b-instruct-q4_k_m.gguf", "baseline")
            == "Qwen2.5-Coder-14B / baseline"
        )
        assert (
            format_db_solver_name("qwen2.5-coder-70b-instruct.gguf", "thinking")
            == "Qwen2.5-Coder-70B / thinking"
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
        assert resolve_folder_solver_name("qwen_14b_baseline") == "Qwen2.5-Coder-14B / baseline"
        assert resolve_folder_solver_name("qwen_7b_guided") == "Qwen2.5-Coder-7B / guided"
        assert resolve_folder_solver_name("qwen_70b_thinking") == "Qwen2.5-Coder-70B / thinking"


class TestDomainEngines:
    @pytest.fixture
    def hypothesis_engine(self):
        return HypothesisTestingEngine()

    @pytest.fixture
    def ecdf_engine(self):
        return EcdfConvergenceEngine()

    @pytest.fixture
    def performance_engine(self):
        return PerformanceMetricsEngine()

    def test_vargha_delaney_a12(self, hypothesis_engine):
        s1 = np.array([1.0, 2.0, 3.0])
        s2 = np.array([4.0, 5.0, 6.0])
        a12, mag = hypothesis_engine.vargha_delaney_a12(s1, s2)
        assert a12 == 1.0  # s1 has all values smaller than s2
        assert mag == "large"

        # Identical samples
        a12_eq, mag_eq = hypothesis_engine.vargha_delaney_a12(s1, s1)
        assert a12_eq == 0.5
        assert mag_eq == "negligible"

    def test_omnibus_and_pairwise_fdr_tests(self, hypothesis_engine):
        # Strongly-typed EvaluationDataset
        bench_data = EvaluationDataset()
        cond = EvaluationCondition(dim=2, noise_std=0.0, problem_id=1)
        for _ in range(5):
            bench_data.add_run(cond, "CMA-ES", RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([10.0, 0.1])))
            bench_data.add_run(cond, "DE", RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([10.0, 0.5])))
            bench_data.add_run(cond, "LLaMEA-14B / baseline", RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([10.0, 0.01])))

        df_omni = hypothesis_engine.run_omnibus_kruskal(bench_data)
        assert not df_omni.empty
        assert len(df_omni) == 1
        assert df_omni.iloc[0]["Problem ID"] == 1
        assert df_omni.iloc[0]["Solvers Count"] == 3

        df_pair = hypothesis_engine.run_pairwise_fdr(bench_data)
        assert not df_pair.empty
        assert len(df_pair) == 3  # (CMA vs DE, CMA vs LLM, DE vs LLM)
        assert "p-adjusted" in df_pair.columns
        assert "Outcome" in df_pair.columns

    def test_compute_convergence_iqr(self, ecdf_engine):
        runs = [
            RunTrace(evaluations=np.array([1, 5, 10]), raw_objectives=np.array([100.0, 50.0, 1.0])),
            RunTrace(evaluations=np.array([1, 5, 10]), raw_objectives=np.array([100.0, 40.0, 2.0])),
            RunTrace(evaluations=np.array([1, 5, 10]), raw_objectives=np.array([100.0, 60.0, 0.5])),
        ]
        eval_grid, med, q25, q75 = ecdf_engine.compute_convergence_iqr(runs, n_points=10)
        assert len(eval_grid) == 10
        assert len(med) == 10
        assert np.all(med >= q25)
        assert np.all(q75 >= med)

    def test_compute_auc_ecdf_matrix(self, ecdf_engine):
        bench_data = EvaluationDataset()
        cond1 = EvaluationCondition(dim=2, noise_std=0.0, problem_id=1)
        cond2 = EvaluationCondition(dim=3, noise_std=0.05, problem_id=8)
        targets = np.logspace(-8, 2, 10)

        for _ in range(3):
            bench_data.add_run(cond1, "CMA-ES", RunTrace(evaluations=np.array([1, 10, 100]), raw_objectives=np.array([10.0, 1.0, 1e-9])))
            bench_data.add_run(cond1, "LLaMEA-14B / baseline", RunTrace(evaluations=np.array([1, 10, 100]), raw_objectives=np.array([10.0, 2.0, 1e-4])))
            bench_data.add_run(cond2, "CMA-ES", RunTrace(evaluations=np.array([1, 10, 100]), raw_objectives=np.array([10.0, 5.0, 1.0])))
            bench_data.add_run(cond2, "LLaMEA-14B / baseline", RunTrace(evaluations=np.array([1, 10, 100]), raw_objectives=np.array([10.0, 8.0, 5.0])))

        solvers = ["CMA-ES", "LLaMEA-14B / baseline"]

        # 1. Group by dim
        df_dim = ecdf_engine.compute_auc_ecdf_matrix(bench_data, solvers, targets, group_by="dim")
        assert not df_dim.empty
        assert "AUC-ECDF (%)" in df_dim.columns
        assert "GroupKey" in df_dim.columns
        assert set(df_dim["GroupKey"].unique()) == {"2D", "3D"}
        assert np.all((df_dim["AUC-ECDF (%)"] >= 0.0) & (df_dim["AUC-ECDF (%)"] <= 100.0))

        # 2. Group by noise_std
        df_noise = ecdf_engine.compute_auc_ecdf_matrix(bench_data, solvers, targets, group_by="noise_std")
        assert not df_noise.empty
        assert "Clean (σ=0.0)" in df_noise["GroupKey"].values
        assert "Noisy (σ=0.05)" in df_noise["GroupKey"].values

        # 3. Problem Grouping
        df_prob = ecdf_engine.compute_auc_ecdf_matrix(bench_data, solvers, targets, group_by="problem_id")
        assert not df_prob.empty
        assert "Sphere (f1)" in df_prob["GroupKey"].values
        assert "Rosenbrock (f8)" in df_prob["GroupKey"].values

        # 4. Group by condition (raw)
        df_cond = ecdf_engine.compute_auc_ecdf_matrix(bench_data, solvers, targets, group_by="condition")
        assert len(df_cond) == 4  # 2 conditions x 2 solvers

    def test_compute_performance_metrics(self, performance_engine):
        runs = [
            RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([10.0, 1e-9])),
            RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([10.0, 1.0])),
        ]
        succ = performance_engine.compute_success_rate(runs, threshold=1e-8)
        assert succ == 0.5


class TestApplicationServicesIntegration:
    def test_selection_service(self):
        session_factory = create_db_session_factory()
        sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
        champions_repo = ChampionsReadRepository(session_factory)
        service = ChampionSelectionService(sqlite_repo=sqlite_repo, champions_repo=champions_repo)
        summary, count = service.get_experiment_balance()
        if (DATA_DIR / "db.sqlite3").exists():
            assert isinstance(summary, pd.DataFrame)
            assert count >= 0

    def test_audit_service(self):
        session_factory = create_db_session_factory()
        sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
        config_repo = EvaluationConfigRepository()
        service = EvaluationAuditService(
            sqlite_repo=sqlite_repo,
            trace_repo=IOHTraceReader(RESULTS_DIR / "ioh_traces"),
            config_repo=config_repo,
        )
        if (DATA_DIR / "db.sqlite3").exists():
            matrix_df, summary = service.get_audit_matrix()
            assert isinstance(matrix_df, pd.DataFrame)
            assert isinstance(summary, dict)
            assert "coverage_pct" in summary
            audit_data = service.get_global_audit_matrix()
            assert isinstance(audit_data.df, pd.DataFrame)
            coverage = audit_data.coverage_summary
            cov_pct = coverage.coverage_pct if isinstance(coverage, AuditCoverageSummary) else coverage["coverage_pct"]
            assert cov_pct >= 0.0

    def test_statistical_service(self):
        session_factory = create_db_session_factory()
        sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
        trace_repo = IOHTraceReader(RESULTS_DIR / "ioh_traces")
        service = StatisticalEvaluationService(sqlite_repo=sqlite_repo, trace_repo=trace_repo)
        if (DATA_DIR / "db.sqlite3").exists():
            df_exp, df_iter = service.get_synthesis_dataframes()
            assert isinstance(df_exp, pd.DataFrame)
            assert isinstance(df_iter, pd.DataFrame)
            traces = service.load_all_traces()
            assert isinstance(traces, EvaluationDataset)


class TestConcreteInfraRepositories:
    def test_sqlite_synthesis_read_repository(self):
        session_factory = create_db_session_factory()
        repo = SQLiteSynthesisReadRepository(session_factory)
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
        repo = IOHTraceReader(RESULTS_DIR / "ioh_traces")
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
        assert "Comprehensive Empirical Evaluation" in report


class TestConvergenceTiers:
    def test_compute_convergence_tiers(self):
        engine = PerformanceMetricsEngine()
        dataset = EvaluationDataset()
        cond = EvaluationCondition(dim=2, noise_std=0.0, problem_id=1)

        # 4 runs with different error levels
        r_solved = RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([100.0, 1e-9]))
        r_moderate = RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([100.0, 1e-4]))
        r_minor = RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([100.0, 0.5]))
        r_stagnated = RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([100.0, 50.0]))

        dataset.add_run(cond, "TestSolver", r_solved)
        dataset.add_run(cond, "TestSolver", r_moderate)
        dataset.add_run(cond, "TestSolver", r_minor)
        dataset.add_run(cond, "TestSolver", r_stagnated)

        df_tiers = engine.compute_convergence_tiers(dataset)
        assert len(df_tiers) == 4
        assert "High Precision (Δy ≤ 10⁻⁸)" in df_tiers["Tier"].values
        assert "Moderate Convergence (10⁻⁸ < Δy ≤ 10⁻²)" in df_tiers["Tier"].values
        assert "Minor Progress (10⁻² < Δy ≤ 1.0)" in df_tiers["Tier"].values
        assert "Severe Stagnation / Failure (Δy > 1.0)" in df_tiers["Tier"].values

    def test_ecdf_matrix_with_dict_targets(self):
        ecdf_engine = EcdfConvergenceEngine()
        dataset = EvaluationDataset()
        cond_clean = EvaluationCondition(dim=2, noise_std=0.0, problem_id=1)
        cond_noisy = EvaluationCondition(dim=2, noise_std=0.05, problem_id=1)

        r1 = RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([10.0, 1e-8]))
        r2 = RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([10.0, 1e-2]))

        dataset.add_run(cond_clean, "TestSolver", r1)
        dataset.add_run(cond_noisy, "TestSolver", r2)

        targets_dict = {
            0.0: np.logspace(-8, 2, 20),
            0.05: np.logspace(-3, 2, 20),
        }

        df_res = ecdf_engine.compute_auc_ecdf_matrix(
            dataset, solvers=["TestSolver"], targets=targets_dict, group_by="condition"
        )
        assert len(df_res) == 2
        assert "AUC-ECDF (%)" in df_res.columns
        assert (df_res["AUC-ECDF (%)"] >= 0.0).all()

    def test_compute_multi_noise_summary(self):
        perf_engine = PerformanceMetricsEngine()
        dataset = EvaluationDataset()

        # Multi-noise levels: 0.0, 0.05, 0.1, 0.2
        for noise in [0.0, 0.05, 0.1, 0.2]:
            cond = EvaluationCondition(dim=2, noise_std=noise, problem_id=1)
            # Solved on clean, degrading with noise
            err = 1e-9 if noise == 0.0 else (1e-4 if noise == 0.05 else (0.5 if noise == 0.1 else 50.0))
            r = RunTrace(evaluations=np.array([1, 100]), raw_objectives=np.array([100.0, err]))
            dataset.add_run(cond, "DynamicSolver", r)

        df_summary = perf_engine.compute_multi_noise_summary(dataset)
        assert len(df_summary) == 4
        assert list(df_summary["Noise Std"]) == [0.0, 0.05, 0.1, 0.2]
        assert df_summary.loc[df_summary["Noise Std"] == 0.0, "Success Rate"].iloc[0] == 1.0
        assert df_summary.loc[df_summary["Noise Std"] == 0.05, "Success Rate"].iloc[0] == 0.0
        assert df_summary.loc[df_summary["Noise Std"] == 0.05, "Fragility Drop"].iloc[0] == 1.0
        assert "Mean Log Error" in df_summary.columns
        assert "Median Error" in df_summary.columns

