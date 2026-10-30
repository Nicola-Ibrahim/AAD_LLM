"""Unit and integration tests for analytics services, domain resolvers, and IOH parsers."""

import numpy as np
import pandas as pd
import pytest

from benchmark.application.model_names import folder_solver_name
from benchmark.application.select_champions import ChampionSelectionService
from benchmark.application.trials.audit import AuditCoverageSummary
from benchmark.domain.enums import (
    BBOB_CLASSES_ORDER,
    BBOBFunction,
)
from benchmark.domain.enums.solver_kind import SolverKind
from benchmark.domain.services.ecdf import EcdfConvergenceEngine
from benchmark.domain.services.hypothesis import HypothesisTestingEngine
from benchmark.domain.services.performance import PerformanceMetricsEngine
from benchmark.domain.services.reliability import search_success_rate
from benchmark.domain.vos import BenchmarkCondition, BenchmarkDataset, RunTrace
from benchmark.infra.io.trace_repository import IOHTraceReader
from benchmark.infra.storage.champions_repository import ChampionsReadRepository
from benchmark.infra.storage.sqlite_repository import SQLiteSynthesisReadRepository
from shared.config import DATA_DIR, RESULTS_DIR
from shared.infra.database import Database


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
        # Strongly-typed BenchmarkDataset
        bench_data = BenchmarkDataset()
        cond = BenchmarkCondition(dim=2, noise_std=0.0, problem_id=1)
        for _ in range(5):
            bench_data.add_run(
                cond,
                "CMA-ES",
                RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([10.0, 0.1])),
            )
            bench_data.add_run(
                cond,
                "DE",
                RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([10.0, 0.5])),
            )
            bench_data.add_run(
                cond,
                "LLaMEA-14B / baseline",
                RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([10.0, 0.01])),
            )

        df_omni = hypothesis_engine.run_omnibus_kruskal(bench_data)
        assert not df_omni.empty
        assert len(df_omni) == 1
        assert df_omni.iloc[0]["Problem ID"] == 1
        assert df_omni.iloc[0]["Solvers Count"] == 3

        df_pair = hypothesis_engine.run_pairwise_fdr(
            bench_data,
            solver_kinds={
                "CMA-ES": SolverKind.CLASSICAL,
                "DE": SolverKind.CLASSICAL,
                "LLaMEA-14B / baseline": SolverKind.GENERATED,
            },
        )
        assert not df_pair.empty
        assert len(df_pair) == 3  # (CMA vs DE, CMA vs LLM, DE vs LLM)
        assert "p-adjusted" in df_pair.columns
        assert "Outcome" in df_pair.columns

    def test_paired_convergence_iqr(self, ecdf_engine):
        runs = [
            RunTrace(evaluations=np.array([1, 5, 10]), raw_objectives=np.array([100.0, 50.0, 1.0])),
            RunTrace(evaluations=np.array([1, 5, 10]), raw_objectives=np.array([100.0, 40.0, 2.0])),
            RunTrace(evaluations=np.array([1, 5, 10]), raw_objectives=np.array([100.0, 60.0, 0.5])),
        ]
        eval_grid = np.logspace(0, 6, 10)
        med, q25, q75, _ = ecdf_engine.compute_trajectory_and_ecdf(
            runs, eval_grid, np.array([1e-8, 1.0])
        )
        assert len(eval_grid) == 10
        assert len(med) == 10
        assert np.all(med >= q25)
        assert np.all(q75 >= med)

    def test_compute_auc_ecdf_matrix(self, ecdf_engine):
        bench_data = BenchmarkDataset()
        cond1 = BenchmarkCondition(dim=2, noise_std=0.0, problem_id=1)
        cond2 = BenchmarkCondition(dim=3, noise_std=0.05, problem_id=8)
        targets = np.logspace(-8, 2, 10)

        for _ in range(3):
            bench_data.add_run(
                cond1,
                "CMA-ES",
                RunTrace(
                    evaluations=np.array([1, 10, 100]), raw_objectives=np.array([10.0, 1.0, 1e-9])
                ),
            )
            bench_data.add_run(
                cond1,
                "LLaMEA-14B / baseline",
                RunTrace(
                    evaluations=np.array([1, 10, 100]), raw_objectives=np.array([10.0, 2.0, 1e-4])
                ),
            )
            bench_data.add_run(
                cond2,
                "CMA-ES",
                RunTrace(
                    evaluations=np.array([1, 10, 100]), raw_objectives=np.array([10.0, 5.0, 1.0])
                ),
            )
            bench_data.add_run(
                cond2,
                "LLaMEA-14B / baseline",
                RunTrace(
                    evaluations=np.array([1, 10, 100]), raw_objectives=np.array([10.0, 8.0, 5.0])
                ),
            )

        solvers = ["CMA-ES", "LLaMEA-14B / baseline"]

        # 1. Group by dim
        df_dim = ecdf_engine.compute_auc_ecdf_matrix(
            bench_data,
            solvers,
            targets,
            budget=100_000,
            group_by="dim",
            solver_kinds={
                "CMA-ES": SolverKind.CLASSICAL,
                "LLaMEA-14B / baseline": SolverKind.GENERATED,
            },
        )
        assert not df_dim.empty
        assert "AUC-ECDF (%)" in df_dim.columns
        assert "GroupKey" in df_dim.columns
        assert set(df_dim["GroupKey"].unique()) == {"2D", "3D"}
        assert np.all((df_dim["AUC-ECDF (%)"] >= 0.0) & (df_dim["AUC-ECDF (%)"] <= 100.0))

        # 2. Group by noise_std
        df_noise = ecdf_engine.compute_auc_ecdf_matrix(
            bench_data,
            solvers,
            targets,
            budget=100_000,
            group_by="noise_std",
            solver_kinds={
                "CMA-ES": SolverKind.CLASSICAL,
                "LLaMEA-14B / baseline": SolverKind.GENERATED,
            },
        )
        assert not df_noise.empty
        assert "Clean (σ=0.0)" in df_noise["GroupKey"].values
        assert "Noisy (σ=0.05)" in df_noise["GroupKey"].values

        # 3. Problem Grouping
        df_prob = ecdf_engine.compute_auc_ecdf_matrix(
            bench_data,
            solvers,
            targets,
            budget=100_000,
            group_by="problem_id",
            solver_kinds={
                "CMA-ES": SolverKind.CLASSICAL,
                "LLaMEA-14B / baseline": SolverKind.GENERATED,
            },
        )
        assert not df_prob.empty
        assert "Sphere (f1)" in df_prob["GroupKey"].values
        assert "Rosenbrock (f8)" in df_prob["GroupKey"].values

        # 4. Group by condition (raw)
        df_cond = ecdf_engine.compute_auc_ecdf_matrix(
            bench_data,
            solvers,
            targets,
            budget=100_000,
            group_by="condition",
            solver_kinds={
                "CMA-ES": SolverKind.CLASSICAL,
                "LLaMEA-14B / baseline": SolverKind.GENERATED,
            },
        )
        assert len(df_cond) == 4  # 2 conditions x 2 solvers

    def test_compute_performance_metrics(self, performance_engine):
        runs = [
            RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([10.0, 1e-9])),
            RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([10.0, 1.0])),
        ]
        succ = search_success_rate(runs, threshold=1e-8)
        assert succ == 0.5


class TestApplicationServicesIntegration:
    def test_selection_service(self):
        session_factory = Database().session_factory
        sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
        summary, count = sqlite_repo.get_experiment_balance()
        if (DATA_DIR / "db.sqlite3").exists():
            assert isinstance(summary, pd.DataFrame)
            assert count >= 0

    def test_audit_service(self):
        from benchmark.application.trials.audit import BenchmarkAuditService
        from benchmark.infra.di import BenchmarkProvider
        from shared.infra.di import container_scope

        with container_scope(BenchmarkProvider(), context={}, request_context={}) as scope:
            snapshot = scope.get(BenchmarkAuditService).get_audit_data().value
        assert isinstance(snapshot.benchmarks, pd.DataFrame)
        assert isinstance(snapshot.synthesis_gaps, pd.DataFrame)
        assert isinstance(snapshot.coverage_summary, AuditCoverageSummary)
        assert snapshot.coverage_summary.coverage_pct >= 0.0

    def test_statistical_service(self):
        session_factory = Database().session_factory
        sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
        trace_repo = IOHTraceReader(RESULTS_DIR / "ioh_traces")
        if (DATA_DIR / "db.sqlite3").exists():
            df_exp, df_iter = sqlite_repo.get_synthesis_dataframes()
            assert isinstance(df_exp, pd.DataFrame)
            assert isinstance(df_iter, pd.DataFrame)
            traces = trace_repo.load_benchmark_traces(solver_resolver=folder_solver_name)
            assert isinstance(traces, BenchmarkDataset)


class TestConcreteInfraRepositories:
    def test_sqlite_synthesis_read_repository(self):
        session_factory = Database().session_factory
        repo = SQLiteSynthesisReadRepository(session_factory)
        if (DATA_DIR / "db.sqlite3").exists():
            df, count = repo.get_experiment_balance()
            assert isinstance(df, pd.DataFrame)
            conditions = repo.get_target_conditions()
            assert isinstance(conditions, list)

    def test_champions_read_repository(self):
        session_factory = Database().session_factory
        repo = ChampionsReadRepository(session_factory)
        if (DATA_DIR / "db.sqlite3").exists():
            service = ChampionSelectionService(champions_repo=repo)
            champs = service.get_champions()
            assert isinstance(champs, dict)
            flat = service.flatten_champions(champs)
            assert isinstance(flat, dict)

    def test_trace_reader(self):
        repo = IOHTraceReader(RESULTS_DIR / "ioh_traces")
        assert hasattr(repo, "load_benchmark_traces")
        assert hasattr(repo, "get_run_count")
        assert hasattr(repo, "parse_dat_file")


class TestNoiseSpecificEcdfTargets:
    def test_ecdf_matrix_with_dict_targets(self):
        ecdf_engine = EcdfConvergenceEngine()
        dataset = BenchmarkDataset()
        cond_clean = BenchmarkCondition(dim=2, noise_std=0.0, problem_id=1)
        cond_noisy = BenchmarkCondition(dim=2, noise_std=0.05, problem_id=1)

        r1 = RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([10.0, 1e-8]))
        r2 = RunTrace(evaluations=np.array([1, 10]), raw_objectives=np.array([10.0, 1e-2]))

        dataset.add_run(cond_clean, "TestSolver", r1)
        dataset.add_run(cond_noisy, "TestSolver", r2)

        targets_dict = {
            0.0: np.logspace(-8, 2, 20),
            0.05: np.logspace(-3, 2, 20),
        }

        df_res = ecdf_engine.compute_auc_ecdf_matrix(
            dataset,
            solvers=["TestSolver"],
            targets=targets_dict,
            budget=100_000,
            group_by="condition",
            solver_kinds={"TestSolver": SolverKind.GENERATED},
        )
        assert len(df_res) == 2
        assert "AUC-ECDF (%)" in df_res.columns
        assert (df_res["AUC-ECDF (%)"] >= 0.0).all()
