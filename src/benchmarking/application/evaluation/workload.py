from pathlib import Path
import hashlib

import pandas as pd

from benchmarking.application.evaluation.constants import (
    EVALUATION_SCHEMA_VERSION,
    ERROR_DEFINITION,
)
from benchmarking.application.interfaces.candidate_code_reader import CandidateCodeReader
from benchmarking.application.interfaces.evaluation_state_store import EvaluationStateStore
from benchmarking.application.interfaces.synthesis_read_repository import SynthesisReadRepository
from benchmarking.application.champions import Champion
from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.application.select_champions import ChampionSelectionService
from evolution.domain.enums import SynthesisMode
from benchmarking.domain.services.resolvers import ModelNames


class EvaluationWorkload:
    """Discover conditions and audit pending benchmark work."""

    def __init__(
        self,
        sqlite_repo: SynthesisReadRepository,
        champion_selection: ChampionSelectionService,
        state_repo: EvaluationStateStore,
        code_reader: CandidateCodeReader,
        model_names: ModelNames,
        config: EvaluationConfig,
    ) -> None:
        self.sqlite_repo = sqlite_repo
        self.champion_selection = champion_selection
        self.state_repo = state_repo
        self.code_reader = code_reader
        self.model_names = model_names
        self.config = config
        self.n_runs = config.target_eval_runs
        self.target_noise_stds = config.target_noise_stds
        self.classical_baselines = config.classical_baselines
        self.baseline_labels = config.baseline_labels

    def _discover_target_conditions(self) -> list[tuple[int, float, int]]:
        """Discover unique (dim, noise_std, problem_id) conditions directly from SQLite or champions."""
        raw_conditions: list[tuple[int, float, int]] = []
        raw_conditions = self.sqlite_repo.get_target_conditions()

        if not raw_conditions:
            champions_flat = self.champion_selection.flatten_champions()
            raw_conditions = [
                (c["dim"], float(c.get("noise_std", 0.0)), c["problem_id"])
                for c in champions_flat.values()
                if "dim" in c and "problem_id" in c
            ]

        if not raw_conditions:
            return []

        # Extract all discovered dimensions, noise standard deviations, and problem IDs
        unique_dims = {c[0] for c in raw_conditions}
        unique_pids = {c[2] for c in raw_conditions}
        if self.target_noise_stds:
            target_noises = sorted(list(set(float(n) for n in self.target_noise_stds)))
        else:
            target_noises = sorted(list({float(c[1]) for c in raw_conditions} | {0.0}))

        expanded = {
            (d, float(n), p) for d in unique_dims for n in target_noises for p in unique_pids
        }
        return sorted(list(expanded))

    # ── Status Inspection Helper ─────────────────────────────────────────────────

    def _inspect_solver_status(
        self,
        target_dir: Path,
        expected_code_hash: str | None = None,
        code_valid: bool = True,
    ) -> tuple[str, int, float | None]:
        """Inspects target directory traces returning (status, runs_found, median_error)."""
        if not code_valid:
            return "MISSING_CODE", 0, None

        if not self.state_repo.solver_directory_exists(target_dir):
            return "PENDING", 0, None

        prov = self.state_repo.read_provenance(target_dir)
        if prov is None:
            return "PENDING", 0, None

        clean_errs = prov.get("errors", prov.get("clean_errors", []))
        runs_found = len(clean_errs)
        med_err = prov.get("median_error", prov.get("median_clean_error"))

        if (
            prov.get("evaluation_schema_version") != EVALUATION_SCHEMA_VERSION
            or prov.get("error_definition") != ERROR_DEFINITION
        ):
            return "NEEDS_RERUN", runs_found, None

        if expected_code_hash and prov.get("code_hash") != expected_code_hash:
            return "NEEDS_RERUN", runs_found, med_err

        if runs_found >= self.n_runs:
            return "COMPLETED", runs_found, med_err
        elif runs_found > 0:
            return "PENDING", runs_found, med_err
        return "PENDING", 0, None

    # ── Workload Auditing Helpers & Builders ────────────────────────────────────

    def _build_champion_audit_row(
        self,
        champ_key: str,
        champ: Champion,
        eval_noise: float,
        is_cross_eval: bool,
    ) -> dict[str, object]:
        """Build standardized workload audit row for a champion or cross-evaluation trial."""
        p_id = champ["problem_id"]
        dim = champ["dim"]
        strat = champ.get("prompt_strategy", "baseline")
        llm_name = champ.get("llm_name", "llamea")
        model_slug = self.model_names.get_model_slug(llm_name)
        native_noise = float(champ.get("noise_std", 0.0))
        raw_mode = champ.get("mode")
        if raw_mode:
            mode_enum = SynthesisMode(raw_mode)
        elif "_implicit" in champ_key:
            mode_enum = SynthesisMode.IMPLICIT
        else:
            mode_enum = SynthesisMode.EXPLICIT

        code_path_raw = Path(champ["code_path"])
        code_valid = self.code_reader.exists(code_path_raw)
        code_hash = (
            hashlib.sha256(self.code_reader.read(code_path_raw).strip().encode("utf-8")).hexdigest()
            if code_valid
            else None
        )

        match mode_enum:
            case SynthesisMode.IMPLICIT:
                solver_folder = f"{model_slug}_{strat}_implicit"
            case SynthesisMode.EXPLICIT:
                if native_noise == 0.0:
                    solver_folder = f"{model_slug}_{strat}"
                else:
                    solver_folder = f"{model_slug}_{strat}_noisy"

        display_suffix = " (cross-eval)" if is_cross_eval else ""

        target_dir = (
            self.state_repo.eval_dir / f"{dim}D" / f"std_{eval_noise}" / f"f{p_id}" / solver_folder
        )
        status, runs_found, med_err = self._inspect_solver_status(
            target_dir, expected_code_hash=code_hash, code_valid=code_valid
        )

        row_key = f"{champ_key}_eval_std{eval_noise}" if is_cross_eval else champ_key
        solver_type = "cross_eval" if is_cross_eval else "champion"

        return {
            "key": row_key,
            "raw_key": champ_key,
            "solver_type": solver_type,
            "solver": solver_folder,
            "display_name": f"{llm_name}{display_suffix}",
            "model": llm_name,
            "strategy": strat,
            "problem_id": p_id,
            "dim": dim,
            "noise_std": eval_noise,
            "mode": mode_enum if not is_cross_eval else SynthesisMode.EXPLICIT,
            "target_runs": self.n_runs,
            "runs_found": runs_found,
            "status": status,
            "median_error": med_err,
            "is_filtered": False,
        }

    # ── Workload Auditing ────────────────────────────────────────────────────────

    def audit_champions_workload(self, include_cross_eval: bool = False) -> pd.DataFrame:
        """Audit LLM champion algorithms (evaluates native environments by default)."""
        champions_flat = self.champion_selection.flatten_champions()
        rows = [
            self._build_champion_audit_row(
                champ_key=k,
                champ=c,
                eval_noise=float(c.get("noise_std", 0.0)),
                is_cross_eval=False,
            )
            for k, c in champions_flat.items()
        ]
        df = pd.DataFrame(rows)
        if include_cross_eval:
            df_cross = self.audit_cross_eval_workload()
            if not df_cross.empty:
                df = pd.concat([df, df_cross], ignore_index=True)
        return df

    def audit_cross_eval_workload(self) -> pd.DataFrame:
        """Audit out-of-distribution cross-environment evaluations for clean champions."""
        champions_flat = self.champion_selection.flatten_champions()
        target_conditions = self._discover_target_conditions()
        noisy_levels = sorted(list({float(c[1]) for c in target_conditions if c[1] > 0.0}))
        if not noisy_levels:
            return pd.DataFrame()

        rows = []
        for k, c in champions_flat.items():
            native_noise = float(c.get("noise_std", 0.0))
            is_clean = native_noise == 0.0 and c.get("mode") == SynthesisMode.EXPLICIT
            if not is_clean:
                continue
            for n_std in noisy_levels:
                rows.append(
                    self._build_champion_audit_row(
                        champ_key=k,
                        champ=c,
                        eval_noise=n_std,
                        is_cross_eval=True,
                    )
                )
        return pd.DataFrame(rows)

    def audit_baselines_workload(self) -> pd.DataFrame:
        """Audit classical baseline algorithms across all target conditions."""
        target_conditions = self._discover_target_conditions()
        rows = []
        for baseline_slug in self.classical_baselines:
            b_name = self.baseline_labels.get(baseline_slug, baseline_slug.upper())
            for dim, noise_std, p_id in target_conditions:
                target_dir = (
                    self.state_repo.eval_dir
                    / f"{dim}D"
                    / f"std_{noise_std}"
                    / f"f{p_id}"
                    / baseline_slug
                )
                status, runs_found, med_err = self._inspect_solver_status(
                    target_dir, expected_code_hash=None, code_valid=True
                )
                rows.append(
                    {
                        "key": f"f{p_id}_{dim}D_std{noise_std}_{baseline_slug}",
                        "solver_type": "baseline",
                        "solver": baseline_slug,
                        "display_name": b_name,
                        "model": baseline_slug,
                        "strategy": "classical",
                        "problem_id": p_id,
                        "dim": dim,
                        "noise_std": noise_std,
                        "mode": SynthesisMode.EXPLICIT,
                        "target_runs": self.n_runs,
                        "runs_found": runs_found,
                        "status": status,
                        "median_error": med_err,
                        "is_filtered": False,
                    }
                )
        return pd.DataFrame(rows)

    def audit_workload(self, solver_type: str = "all") -> pd.DataFrame:
        """Comprehensive workload audit across configured solver types ('all', 'champions', 'cross_eval', 'baselines')."""
        dfs = []
        if solver_type in ("all", "champions"):
            dfs.append(self.audit_champions_workload())
        if solver_type in ("all", "cross_eval"):
            dfs.append(self.audit_cross_eval_workload())
        if solver_type in ("all", "baselines"):
            dfs.append(self.audit_baselines_workload())

        if not dfs:
            return pd.DataFrame()
        return pd.concat(dfs, ignore_index=True)
