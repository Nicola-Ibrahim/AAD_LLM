"""Statistical Evaluation Application Service (Notebooks 07 & 08 Use Cases).

Coordinates trace dataset ingestion, omnibus Kruskal-Wallis & pairwise FDR tests,
Vargha-Delaney A12 effect size computations, convergence IQR curves, and markdown reporting.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd

from benchmarking.domain.services.ecdf import EcdfConvergenceEngine
from benchmarking.domain.services.hypothesis import HypothesisTestingEngine
from benchmarking.domain.services.performance import PerformanceMetricsEngine
from benchmarking.domain.services.resolvers import resolve_folder_solver_name
from benchmarking.domain.vos import EvaluationDataset, RunTrace
from benchmarking.infra.io.trace_repository import IOHTraceReader
from benchmarking.infra.storage.sqlite_repository import SQLiteSynthesisReadRepository


def generate_markdown_report(
    df_omnibus: pd.DataFrame | None = None,
    df_pairwise: pd.DataFrame | None = None,
    output_path: Path | None = None,
    omnibus_df: pd.DataFrame | None = None,
    pairwise_df: pd.DataFrame | None = None,
    **kwargs: Any,
) -> str:
    """Generate scientific Markdown summary report documenting statistical test results."""
    o_df = df_omnibus if df_omnibus is not None else (omnibus_df if omnibus_df is not None else pd.DataFrame())
    p_df = df_pairwise if df_pairwise is not None else (pairwise_df if pairwise_df is not None else pd.DataFrame())

    report_lines: list[str] = [
        "# Comprehensive Empirical Evaluation & Statistical Analysis Report",
        "",
        "## 1. Overview & Experimental Protocol",
        "- **Benchmark Suite**: BBOB (Black-Box Optimization Benchmarking)",
        "- **Statistical Protocols**: Kruskal-Wallis H-test (omnibus), Mann-Whitney U test (pairwise)",
        "- **Multiplicity Correction**: Benjamini-Hochberg False Discovery Rate (FDR, $\\alpha=0.05$)",
        "- **Effect Size Metric**: Vargha-Delaney $\\hat{A}_{12}$ non-parametric effect size",
        "",
    ]

    if not o_df.empty:
        total_tests = len(o_df)
        sig_tests = int(cast(Any, o_df["Significant"] == "Yes").sum()) if "Significant" in o_df.columns else 0
        report_lines.extend([
            "## 2. Omnibus Kruskal-Wallis Significance Summary",
            f"- **Total Experimental Conditions Evaluated**: {total_tests}",
            f"- **Statistically Significant omnibus Differences ($p < 0.05$)**: {sig_tests} / {total_tests} ({(sig_tests / max(1, total_tests) * 100):.1f}%)",
            "",
            "### Omnibus Differences by Problem Dimension",
        ])
        if "Dim" in o_df.columns:
            for dim, group in o_df.groupby("Dim"):
                d_sig = int(cast(Any, group["Significant"] == "Yes").sum())
                report_lines.append(f"- **{dim}D**: {d_sig} / {len(group)} conditions reject null hypothesis")
        report_lines.append("")

    if not p_df.empty:
        total_pw = len(p_df)
        sig_pw = int(cast(Any, p_df["Significant (FDR)"]).sum()) if "Significant (FDR)" in p_df.columns else 0
        report_lines.extend([
            "## 3. Pairwise Comparisons & FDR Correction",
            f"- **Total Pairwise Hypothesis Tests**: {total_pw}",
            f"- **Significant Differences after FDR Correction ($\\alpha=0.05$)**: {sig_pw} / {total_pw} ({(sig_pw / max(1, total_pw) * 100):.1f}%)",
            "",
            "### Comparison Tier Breakdown",
        ])
        if "Comparison Tier" in p_df.columns:
            for tier, group in p_df.groupby("Comparison Tier"):
                t_sig = int(cast(Any, group["Significant (FDR)"]).sum())
                report_lines.append(f"- **{tier}**: {t_sig} / {len(group)} pairs significant")
        report_lines.append("")

    if output_path is not None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(report_lines), encoding="utf-8")

    return "\n".join(report_lines)


class StatisticalEvaluationService:
    """Application service for statistical hypothesis testing, effect sizes, and reporting."""

    def __init__(
        self,
        sqlite_repo: SQLiteSynthesisReadRepository,
        trace_repo: IOHTraceReader | None = None,
        hypothesis_engine: HypothesisTestingEngine | None = None,
        ecdf_engine: EcdfConvergenceEngine | None = None,
        performance_engine: PerformanceMetricsEngine | None = None,
    ):
        self.sqlite_repo = sqlite_repo
        self.trace_repo = trace_repo or IOHTraceReader()
        self.hypothesis_engine = hypothesis_engine or HypothesisTestingEngine()
        self.ecdf_engine = ecdf_engine or EcdfConvergenceEngine()
        self.performance_engine = performance_engine or PerformanceMetricsEngine()

    def get_synthesis_dataframes(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Query synthesis database for completed experiment metadata and iteration metrics."""
        return self.sqlite_repo.get_synthesis_dataframes()

    def load_evaluation_traces(
        self,
        dims: list[int] | None = None,
        problems: list[int] | None = None,
        noise_stds: list[float] | None = None,
        solvers: list[str] | None = None,
        solver_resolver: Callable[[str], str] | None = resolve_folder_solver_name,
    ) -> EvaluationDataset:
        """Ingest raw IOHprofiler evaluation traces into a structured EvaluationDataset."""
        return self.trace_repo.load_evaluation_traces(
            dims=dims,
            problems=problems,
            noise_stds=noise_stds,
            solvers=solvers,
            solver_resolver=solver_resolver or resolve_folder_solver_name,
        )

    def load_all_traces(self) -> EvaluationDataset:
        """Load all available benchmark evaluation traces across all conditions."""
        return self.load_evaluation_traces()

    def load_filtered_traces(
        self,
        dims: list[int],
        problems: list[int],
        noise_stds: list[float],
        solvers: list[str] | None = None,
    ) -> EvaluationDataset:
        """Load benchmark evaluation traces for explicitly specified dimensions, problems, and noise levels."""
        return self.load_evaluation_traces(
            dims=dims,
            problems=problems,
            noise_stds=noise_stds,
            solvers=solvers,
        )

    def run_omnibus_kruskal(
        self,
        benchmark_data: EvaluationDataset,
    ) -> pd.DataFrame:
        """Execute omnibus Kruskal-Wallis H-tests across all solvers per problem condition."""
        return self.hypothesis_engine.run_omnibus_kruskal(benchmark_data)

    def run_pairwise_fdr(
        self,
        benchmark_data: EvaluationDataset,
        alpha: float = 0.05,
    ) -> pd.DataFrame:
        """Execute pairwise Mann-Whitney U tests with Benjamini-Hochberg FDR correction."""
        return self.hypothesis_engine.run_pairwise_fdr(benchmark_data, alpha=alpha)

    def compute_convergence_iqr(
        self,
        runs: list[RunTrace],
        max_evals: int = 1000000,
        n_points: int = 100,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Compute median, 25th, and 75th percentile convergence curves across runs."""
        return self.ecdf_engine.compute_convergence_iqr(runs, max_evals=max_evals, n_points=n_points)

    def compute_synthesis_transfer_correlation(
        self,
        df_exp: pd.DataFrame,
    ) -> tuple[float, float]:
        """Compute Pearson correlation between synthesis error and empirical evaluation error."""
        return self.hypothesis_engine.compute_synthesis_transfer_correlation(df_exp)

    def compute_success_rate(
        self,
        runs: list[RunTrace],
        threshold: float = 1e-8,
    ) -> float:
        """Compute empirical success rate (fraction of runs reaching delta_y <= threshold)."""
        return self.performance_engine.compute_success_rate(runs, threshold=threshold)

    def compute_fragility_matrix(
        self,
        benchmark_data: EvaluationDataset,
        dim: int,
        solvers: list[str],
        problem_ids: list[int],
        clean_std: float = 0.0,
        noisy_std: float = 0.05,
        threshold: float = 1e-8,
    ) -> tuple[np.ndarray, list[str]]:
        """Compute the Fragility Index matrix (Clean Success Rate - Noisy Success Rate) per problem & solver."""
        return self.performance_engine.compute_fragility_matrix(
            benchmark_data=benchmark_data,
            dim=dim,
            solvers=solvers,
            problem_ids=problem_ids,
            clean_std=clean_std,
            noisy_std=noisy_std,
            threshold=threshold,
        )

    def compute_hardness_success_rates(
        self,
        benchmark_data: EvaluationDataset,
        dim: int,
        solvers_list: list[str],
        noise_level: float,
        threshold: float = 1e-8,
    ) -> pd.DataFrame:
        """Aggregate solver success rates grouped by BBOB landscape hardness class."""
        return self.performance_engine.compute_hardness_success_rates(
            benchmark_data=benchmark_data,
            dim=dim,
            solvers_list=solvers_list,
            noise_level=noise_level,
            threshold=threshold,
        )

    def compute_validation_medians(
        self,
        benchmark_data: EvaluationDataset,
        dim: int,
        problem_ids: list[int],
        clean_std: float = 0.0,
        noisy_std: float = 0.05,
    ) -> tuple[list[float], list[float], list[str]]:
        """Compute median terminal error across all solvers for Clean vs. Noisy validation."""
        return self.performance_engine.compute_validation_medians(
            benchmark_data=benchmark_data,
            dim=dim,
            problem_ids=problem_ids,
            clean_std=clean_std,
            noisy_std=noisy_std,
        )

    def compute_trajectory_and_ecdf(
        self,
        runs: list[RunTrace],
        eval_grid: np.ndarray,
        targets: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Compute convergence trajectory (median, Q25, Q75) and ECDF empirical curve."""
        return self.ecdf_engine.compute_trajectory_and_ecdf(
            runs=runs,
            eval_grid=eval_grid,
            targets=targets,
        )

    def compute_robustness_profile(
        self,
        benchmark_data: EvaluationDataset,
        dim: int,
        solvers_order: list[str],
        problem_ids: list[int],
        clean_std: float = 0.0,
        noisy_std: float = 0.05,
        threshold: float = 1e-8,
    ) -> tuple[list[str], list[float], list[float], list[float]]:
        """Compute clean vs. noisy success rates and delta robustness drops across solvers."""
        return self.performance_engine.compute_robustness_profile(
            benchmark_data=benchmark_data,
            dim=dim,
            solvers_order=solvers_order,
            problem_ids=problem_ids,
            clean_std=clean_std,
            noisy_std=noisy_std,
            threshold=threshold,
        )

    def compute_scaffolding_ablation(
        self,
        benchmark_data: EvaluationDataset,
        dim: int,
        solvers_list: list[str],
        problem_ids: list[int],
        clean_std: float = 0.0,
        noisy_std: float = 0.05,
        threshold: float = 1e-8,
    ) -> tuple[list[str], list[float], list[float]]:
        """Compute prompt scaffolding ablation success rates for a model family."""
        return self.performance_engine.compute_scaffolding_ablation(
            benchmark_data=benchmark_data,
            dim=dim,
            solvers_list=solvers_list,
            problem_ids=problem_ids,
            clean_std=clean_std,
            noisy_std=noisy_std,
            threshold=threshold,
        )

    def compute_auc_ecdf_ranking(
        self,
        benchmark_data: EvaluationDataset,
        solvers: list[str],
        targets: np.ndarray,
        n_grid_points: int = 200,
    ) -> pd.DataFrame:
        """Compute Area Under the Runtime ECDF Curve (AUC-ECDF) for each solver across all conditions."""
        return self.ecdf_engine.compute_auc_ecdf_ranking(
            benchmark_data=benchmark_data,
            solvers=solvers,
            targets=targets,
            n_grid_points=n_grid_points,
        )

    def compute_auc_ecdf_matrix(
        self,
        benchmark_data: EvaluationDataset,
        solvers: list[str],
        targets: np.ndarray,
        group_by: str = "dim",
        n_grid_points: int = 200,
    ) -> pd.DataFrame:
        """Compute Area Under the Runtime ECDF Curve (AUC-ECDF) disaggregated by grouping axis."""
        return self.ecdf_engine.compute_auc_ecdf_matrix(
            benchmark_data=benchmark_data,
            solvers=solvers,
            targets=targets,
            group_by=group_by,  # type: ignore[arg-type]
            n_grid_points=n_grid_points,
        )

    def generate_markdown_report(
        self,
        df_omnibus: pd.DataFrame | None = None,
        df_pairwise: pd.DataFrame | None = None,
        output_path: Path | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate formatted Markdown report summarizing statistical significance and effect sizes."""
        return generate_markdown_report(
            df_omnibus=df_omnibus,
            df_pairwise=df_pairwise,
            output_path=output_path,
            **kwargs,
        )
