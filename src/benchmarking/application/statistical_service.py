"""Statistical Evaluation Application Service (Notebooks 07 & 08 Use Cases).

Coordinates trace dataset ingestion, omnibus Kruskal-Wallis & pairwise FDR tests,
Vargha-Delaney A12 effect size computations, convergence IQR curves, and markdown reporting.
"""

from pathlib import Path
import numpy as np
import pandas as pd

from benchmarking.domain.resolvers import resolve_folder_solver_name
from benchmarking.domain.statistics import StatisticalEngine
from benchmarking.infra.io.trace_repository import IOHTraceReader
from benchmarking.infra.storage.sqlite_repository import SQLiteBenchmarkReadRepository


from typing import Any


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
        "- **Effect Size Metric**: Vargha-Delaney $\\hat{A}_{12}$ statistic",
        "",
        "## 2. Omnibus Kruskal-Wallis Test Summary",
        "",
    ]

    def _df_to_markdown(df: pd.DataFrame) -> str:
        try:
            return df.to_markdown(index=False)
        except Exception:
            headers = [str(c) for c in df.columns]
            lines = [
                "| " + " | ".join(headers) + " |",
                "| " + " | ".join(["---"] * len(headers)) + " |",
            ]
            for _, row in df.iterrows():
                row_str = [str(val) for val in row]
                lines.append("| " + " | ".join(row_str) + " |")
            return "\n".join(lines)

    if not o_df.empty:
        total_tests = len(o_df)
        sig_tests = len(o_df[o_df["Significant"] == "Yes"])
        sig_pct = (sig_tests / total_tests * 100) if total_tests > 0 else 0.0

        report_lines.extend([
            f"- **Total Experimental Conditions Analyzed**: {total_tests}",
            f"- **Statistically Significant Differences Found**: {sig_tests} ({sig_pct:.1f}%)",
            "",
            "### Omnibus Results Table",
            _df_to_markdown(o_df),
            "",
        ])

    if not p_df.empty:
        report_lines.extend([
            "## 3. Pairwise Statistical Comparisons (FDR-Corrected)",
            "",
            _df_to_markdown(p_df.head(25)),
            "",
        ])

    full_report = "\n".join(report_lines)
    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(full_report, encoding="utf-8")

    return full_report


class StatisticalEvaluationService:
    """Application use case for statistical hypothesis testing, effect sizes, and convergence analysis."""

    def __init__(
        self,
        sqlite_repo: SQLiteBenchmarkReadRepository,
        trace_repo: IOHTraceReader,
        engine: StatisticalEngine | None = None,
    ):
        self.sqlite_repo = sqlite_repo
        self.trace_repo = trace_repo
        self.engine = engine or StatisticalEngine()

    def get_synthesis_dataframes(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Load synthesis experiments and iterations tables into pandas DataFrames."""
        return self.sqlite_repo.get_synthesis_dataframes()

    def load_evaluation_traces(
        self,
        dims: list[int] | None = None,
        problems: list[int] | None = None,
        noise_stds: list[float] | None = None,
        solvers: list[str] | None = None,
    ) -> dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]]:
        """Scans evaluations directory and loads all .dat runs organized by condition key."""
        return self.trace_repo.load_evaluation_traces(
            dims=dims,
            problems=problems,
            noise_stds=noise_stds,
            solvers=solvers,
            solver_resolver=resolve_folder_solver_name,
        )

    def run_omnibus_kruskal(
        self,
        benchmark_data: dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]],
    ) -> pd.DataFrame:
        """Execute omnibus Kruskal-Wallis $H$-test across all conditions."""
        return self.engine.run_omnibus_kruskal(benchmark_data)

    def run_pairwise_fdr(
        self,
        benchmark_data: dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]],
        alpha: float = 0.05,
    ) -> pd.DataFrame:
        """Execute pairwise Mann-Whitney U tests with Benjamini-Hochberg FDR correction and A12."""
        return self.engine.run_pairwise_fdr(benchmark_data, alpha=alpha)

    def compute_convergence_iqr(
        self,
        runs: list[tuple[np.ndarray, np.ndarray]],
        max_evals: int = 1000000,
        n_points: int = 100,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Compute median, 25th, and 75th percentile convergence curves across runs."""
        return self.engine.compute_convergence_iqr(runs, max_evals=max_evals, n_points=n_points)

    def compute_synthesis_transfer_correlation(
        self,
        df_exp: pd.DataFrame,
    ) -> tuple[float, float]:
        """Compute Pearson correlation between synthesis error and empirical evaluation error."""
        return self.engine.compute_synthesis_transfer_correlation(df_exp)

    def compute_success_rate(
        self,
        runs: list[tuple[np.ndarray, np.ndarray]],
        threshold: float = 1e-8,
    ) -> float:
        """Compute empirical success rate (fraction of runs reaching delta_y <= threshold)."""
        return self.engine.compute_success_rate(runs, threshold=threshold)

    def compute_fragility_matrix(
        self,
        benchmark_data: dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]],
        dim: int,
        solvers: list[str],
        problem_ids: list[int],
        clean_std: float = 0.0,
        noisy_std: float = 0.05,
        threshold: float = 1e-8,
    ) -> tuple[np.ndarray, list[str]]:
        """Compute the Fragility Index matrix (Clean Success Rate - Noisy Success Rate) per problem & solver."""
        return self.engine.compute_fragility_matrix(
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
        benchmark_data: dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]],
        dim: int,
        solvers_list: list[str],
        noise_level: float,
        threshold: float = 1e-8,
    ) -> pd.DataFrame:
        """Aggregate solver success rates grouped by BBOB landscape hardness class."""
        return self.engine.compute_hardness_success_rates(
            benchmark_data=benchmark_data,
            dim=dim,
            solvers_list=solvers_list,
            noise_level=noise_level,
            threshold=threshold,
        )

    def compute_validation_medians(
        self,
        benchmark_data: dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]],
        dim: int,
        problem_ids: list[int],
        clean_std: float = 0.0,
        noisy_std: float = 0.05,
    ) -> tuple[list[float], list[float], list[str]]:
        """Compute median terminal error across all solvers for Clean vs. Noisy validation."""
        return self.engine.compute_validation_medians(
            benchmark_data=benchmark_data,
            dim=dim,
            problem_ids=problem_ids,
            clean_std=clean_std,
            noisy_std=noisy_std,
        )

    def compute_trajectory_and_ecdf(
        self,
        runs: list[tuple[np.ndarray, np.ndarray]],
        eval_grid: np.ndarray,
        targets: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Compute convergence trajectory (median, Q25, Q75) and ECDF empirical curve."""
        return self.engine.compute_trajectory_and_ecdf(
            runs=runs,
            eval_grid=eval_grid,
            targets=targets,
        )

    def compute_robustness_profile(
        self,
        benchmark_data: dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]],
        dim: int,
        solvers_order: list[str],
        problem_ids: list[int],
        clean_std: float = 0.0,
        noisy_std: float = 0.05,
        threshold: float = 1e-8,
    ) -> tuple[list[str], list[float], list[float], list[float]]:
        """Compute clean vs. noisy success rates and delta robustness drops across solvers."""
        return self.engine.compute_robustness_profile(
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
        benchmark_data: dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]],
        dim: int,
        solvers_list: list[str],
        problem_ids: list[int],
        clean_std: float = 0.0,
        noisy_std: float = 0.05,
        threshold: float = 1e-8,
    ) -> tuple[list[str], list[float], list[float]]:
        """Compute prompt scaffolding ablation success rates for a model family."""
        return self.engine.compute_scaffolding_ablation(
            benchmark_data=benchmark_data,
            dim=dim,
            solvers_list=solvers_list,
            problem_ids=problem_ids,
            clean_std=clean_std,
            noisy_std=noisy_std,
            threshold=threshold,
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
