"""Benchmark Audit Application Service (Notebook 06 Use Case).

Coordinates multi-model, multi-strategy coverage matrix analysis across all 30 BBOB conditions.
"""

import re
from typing import Any
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from benchmarking.domain.enums import BBOBFunction
from benchmarking.domain.services.resolvers import get_clean_model_label, get_model_slug
from benchmarking.infra.io.trace_repository import IOHTraceReader
from benchmarking.infra.storage.config_repository import EvaluationConfigRepository
from benchmarking.infra.storage.sqlite_repository import SQLiteSynthesisReadRepository


class AuditCoverageSummary(BaseModel):
    """Strongly-typed summary of benchmark grid coverage."""

    total_conditions: int = 0
    total_models: int = 0
    total_cells: int = 0
    completed_cells: int = 0
    partial_cells: int = 0
    missing_cells: int = 0
    coverage_pct: float = 0.0


class AuditMatrixData(BaseModel):
    """Strongly-typed Pydantic model for global benchmark coverage audit results."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    df: pd.DataFrame = Field(default_factory=pd.DataFrame)
    df_exp: pd.DataFrame = Field(default_factory=pd.DataFrame)
    df_iter: pd.DataFrame = Field(default_factory=pd.DataFrame)
    all_solvers: list[str] = Field(default_factory=list)
    classical_solvers: list[str] = Field(default_factory=list)
    llm_solvers: list[str] = Field(default_factory=list)
    model_families: list[str] = Field(default_factory=list)
    dims: list[int] = Field(default_factory=list)
    noise_levels: list[float] = Field(default_factory=list)
    problem_ids: list[int] = Field(default_factory=list)
    eval_counts: dict[Any, Any] = Field(default_factory=dict)
    coverage_summary: AuditCoverageSummary | dict[str, Any] = Field(default_factory=dict)


class EvaluationAuditService:
    """Application use case for auditing global benchmark evaluation completion and coverage."""

    def __init__(
        self,
        sqlite_repo: SQLiteSynthesisReadRepository,
        trace_repo: IOHTraceReader,
        config_repo: EvaluationConfigRepository,
    ):
        self.sqlite_repo = sqlite_repo
        self.trace_repo = trace_repo
        self.config_repo = config_repo

        cfg = self.config_repo.load_config()
        self.target_runs = int(cfg.get("target_eval_runs", 20))
        self.classical_baselines = cfg.get("classical_baselines", ["cmaes", "de", "pso"])

    def get_audit_matrix(self) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Generate the complete 30-condition audit matrix across discovered models and baselines."""
        df_db = self.sqlite_repo.get_completed_experiments_matrix()
        if df_db.empty:
            return pd.DataFrame(), {}

        unique_conditions = (
            df_db[["dim", "noise_std", "problem_id"]]
            .drop_duplicates()
            .sort_values(by=["dim", "noise_std", "problem_id"])
        )
        unique_models = sorted(df_db["llm_name"].dropna().unique())
        strategies = ["baseline", "guided", "thinking", "vectorization"]
        baselines = self.classical_baselines

        matrix_rows: list[dict[str, Any]] = []
        total_cells = 0
        completed_cells = 0
        partial_cells = 0
        missing_cells = 0

        for _, cond in unique_conditions.iterrows():
            dim = int(cond["dim"])
            noise_std = float(cond["noise_std"])
            p_id = int(cond["problem_id"])

            row: dict[str, Any] = {
                "Dim": f"{dim}D",
                "Noise": f"std_{noise_std}",
                "Problem": BBOBFunction.get_name(p_id),
                "Class": BBOBFunction.get_class(p_id),
            }

            # 1. Classical Baselines
            for b in baselines:
                total_cells += 1
                b_dir = self.trace_repo.eval_dir / f"{dim}D" / f"std_{noise_std}" / f"f{p_id}" / b
                runs = self.trace_repo.get_run_count(b_dir) if b_dir.exists() else 0
                col_name = f"Baseline / {b.upper()}"

                if runs >= self.target_runs:
                    row[col_name] = f"✅ {runs}/{self.target_runs}"
                    completed_cells += 1
                elif runs > 0:
                    row[col_name] = f"⚠️ {runs}/{self.target_runs}"
                    partial_cells += 1
                else:
                    row[col_name] = "❌ 0"
                    missing_cells += 1

            # 2. Model Strategies
            for llm_name in unique_models:
                m_label = get_clean_model_label(llm_name)
                m_slug = get_model_slug(llm_name)

                for strat in strategies:
                    total_cells += 1
                    col_name = f"{m_label} / {strat}"
                    folder_name = f"{m_slug}_{strat}"
                    s_dir = self.trace_repo.eval_dir / f"{dim}D" / f"std_{noise_std}" / f"f{p_id}" / folder_name
                    runs = self.trace_repo.get_run_count(s_dir) if s_dir.exists() else 0

                    if runs >= self.target_runs:
                        row[col_name] = f"✅ {runs}/{self.target_runs}"
                        completed_cells += 1
                    elif runs > 0:
                        row[col_name] = f"⚠️ {runs}/{self.target_runs}"
                        partial_cells += 1
                    else:
                        row[col_name] = "❌ 0"
                        missing_cells += 1

            matrix_rows.append(row)

        df_matrix = pd.DataFrame(matrix_rows)
        coverage_pct = (completed_cells / total_cells * 100.0) if total_cells > 0 else 0.0

        summary = {
            "total_conditions": len(unique_conditions),
            "total_models": len(unique_models),
            "total_cells": total_cells,
            "completed_cells": completed_cells,
            "partial_cells": partial_cells,
            "missing_cells": missing_cells,
            "coverage_pct": coverage_pct,
        }

        return df_matrix, summary

    def get_global_audit_matrix(self) -> AuditMatrixData:
        """Generate the complete 30-condition audit matrix with Pydantic model access."""
        df_matrix, summary = self.get_audit_matrix()
        df_exp, df_iter = self.sqlite_repo.get_synthesis_dataframes()

        if df_matrix.empty:
            return AuditMatrixData(
                df=pd.DataFrame(),
                df_exp=df_exp,
                df_iter=df_iter,
                all_solvers=[],
                dims=[],
                noise_levels=[],
                problem_ids=[],
                eval_counts={},
                coverage_summary=summary,
            )

        solver_cols = [c for c in df_matrix.columns if c not in ["Dim", "Noise", "Problem", "Class"]]
        dims = sorted(list({int(d.replace("D", "")) for d in df_matrix["Dim"]}))
        noise_levels = sorted(list({float(n.replace("std_", "")) for n in df_matrix["Noise"]}))
        problem_ids = sorted(list({int(re.search(r"f(\d+)", p).group(1)) for p in df_matrix["Problem"] if re.search(r"f(\d+)", p)}))

        eval_counts: dict[Any, Any] = {}
        for _, row in df_matrix.iterrows():
            d = int(row["Dim"].replace("D", ""))
            n = float(row["Noise"].replace("std_", ""))
            p_m = re.search(r"f(\d+)", row["Problem"])
            p = int(p_m.group(1)) if p_m else 1

            if (d, n, p) not in eval_counts:
                eval_counts[(d, n, p)] = {}

            for s in solver_cols:
                val = str(row[s])
                cnt_m = re.search(r"(\d+)/", val)
                cnt = int(cnt_m.group(1)) if cnt_m else 0
                eval_counts[(d, n, p)][s] = cnt
                eval_counts[(d, n, p, s)] = cnt

        classical_solvers = [s for s in solver_cols if s.startswith("Baseline")]
        llm_solvers = [s for s in solver_cols if not s.startswith("Baseline")]
        model_families = sorted(list({s.split(" / ")[0] for s in llm_solvers}))

        return AuditMatrixData(
            df=df_matrix,
            df_exp=df_exp,
            df_iter=df_iter,
            all_solvers=solver_cols,
            classical_solvers=classical_solvers,
            llm_solvers=llm_solvers,
            model_families=model_families,
            dims=dims,
            noise_levels=noise_levels,
            problem_ids=problem_ids,
            eval_counts=eval_counts,
            coverage_summary=AuditCoverageSummary(**summary),
        )
