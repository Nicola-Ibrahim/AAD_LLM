import hashlib
from pathlib import Path

import pandas as pd

from benchmarking.application.champions import Champion, GenerationMode
from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.application.interfaces.candidate_code_reader import CandidateCodeReader
from benchmarking.application.interfaces.evaluation_state_store import EvaluationStateStore
from benchmarking.application.interfaces.synthesis_read_repository import SynthesisReadRepository
from benchmarking.application.select_champions import ChampionSelectionService
from benchmarking.domain.services.condition_status import ConditionStatus, inspect_condition
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
        planned_target_conditions: tuple[tuple[int, float, int], ...] = (),
    ) -> None:
        self.sqlite_repo = sqlite_repo
        self.champion_selection = champion_selection
        self.state_repo = state_repo
        self.code_reader = code_reader
        self.model_names = model_names
        self.config = config
        self.planned_target_conditions = planned_target_conditions
        self.n_runs = config.target_eval_runs
        self.target_noise_stds = config.target_noise_stds
        self.classical_baselines = config.classical_baselines
        self.baseline_labels = config.baseline_labels

    def _discover_target_conditions(self) -> list[tuple[int, float, int]]:
        """Discover unique (dim, noise_std, problem_id) conditions directly from SQLite or champions."""
        raw_conditions = self.sqlite_repo.get_target_conditions()

        if not raw_conditions:
            champions_flat = self.champion_selection.flatten_champions()
            raw_conditions = [
                (c["dim"], float(c.get("noise_std", 0.0)), c["problem_id"])
                for c in champions_flat.values()
                if "dim" in c and "problem_id" in c
            ]

        if not raw_conditions:
            raw_conditions = list(self.planned_target_conditions)
        if not raw_conditions:
            return []

        # Extract all discovered dimensions, noise standard deviations, and problem IDs
        unique_dims = {c[0] for c in raw_conditions}
        unique_pids = {c[2] for c in raw_conditions}
        if self.config.cross_function_enabled:
            unique_pids.update(self.config.cross_function_problem_ids)
        if self.target_noise_stds:
            target_noises = sorted(list(set(float(n) for n in self.target_noise_stds)))
        else:
            target_noises = sorted(list({float(c[1]) for c in raw_conditions} | {0.0}))
        if self.config.cross_function_enabled:
            target_noises = sorted(set(target_noises) | {0.0})

        expanded = {
            (d, float(n), p) for d in unique_dims for n in target_noises for p in unique_pids
        }
        return sorted(list(expanded))

    # ── Status Inspection Helper ─────────────────────────────────────────────────

    def inspect_status(
        self, target_dir: Path, expected_code_hash: str | None = None, code_valid: bool = True
    ) -> ConditionStatus:
        return inspect_condition(
            code_available=code_valid,
            directory_exists=self.state_repo.solver_directory_exists(target_dir),
            provenance=self.state_repo.read_provenance(target_dir),
            expected_code_hash=expected_code_hash,
            expected_trials=self.n_runs,
        )

    # ── Workload Auditing Helpers & Builders ────────────────────────────────────

    def _build_champion_audit_row(
        self,
        champ_key: str,
        champ: Champion,
        eval_noise: float,
        is_noise_robustness: bool,
        target_problem_id: int | None = None,
    ) -> dict[str, object]:
        """Build a native, noise-robustness, or source–target transfer audit row."""
        source_problem_id = champ["problem_id"]
        p_id = source_problem_id if target_problem_id is None else target_problem_id
        dim = champ["dim"]
        strat = champ.get("prompt_strategy", "baseline")
        llm_name = champ.get("llm_name", "llamea")
        model_slug = self.model_names.get_model_slug(llm_name)
        native_noise = float(champ.get("noise_std", 0.0))
        raw_mode = champ.get("mode")
        if raw_mode:
            mode_enum = GenerationMode(raw_mode)
        elif "_implicit" in champ_key:
            mode_enum = GenerationMode.IMPLICIT
        else:
            mode_enum = GenerationMode.EXPLICIT

        code_path_raw = Path(champ["code_path"])
        code_valid = self.code_reader.exists(code_path_raw)
        code_hash = (
            hashlib.sha256(self.code_reader.read(code_path_raw).strip().encode("utf-8")).hexdigest()
            if code_valid
            else None
        )

        match mode_enum:
            case GenerationMode.IMPLICIT:
                solver_folder = f"{model_slug}_{strat}_implicit"
            case GenerationMode.EXPLICIT:
                if native_noise == 0.0:
                    solver_folder = f"{model_slug}_{strat}"
                else:
                    solver_folder = f"{model_slug}_{strat}_noisy"

        display_suffix = " (noise robustness)" if is_noise_robustness else ""

        target_dir = (
            self.state_repo.eval_dir / f"{dim}D" / f"std_{eval_noise}" / f"f{p_id}" / solver_folder
        )
        if target_problem_id is not None and p_id != source_problem_id:
            target_dir = (
                self.state_repo.eval_dir.parent
                / "cross_function_traces"
                / f"source_f{source_problem_id}"
                / f"{dim}D"
                / f"std_{eval_noise}"
                / f"f{p_id}"
                / f"{solver_folder}_{(code_hash or 'missing')[:12]}"
            )
        if target_problem_id is not None:
            display_suffix = f" (f{source_problem_id} → f{p_id})"
        inspection = self.inspect_status(
            target_dir, expected_code_hash=code_hash, code_valid=code_valid
        )

        row_key = f"{champ_key}_eval_std{eval_noise}" if is_noise_robustness else champ_key
        solver_type = "noise_robustness" if is_noise_robustness else "champion"
        if target_problem_id is not None:
            solver_type = "cross_function"
            row_key = f"{champ_key}_target_f{p_id}"

        return {
            "key": row_key,
            "raw_key": champ_key,
            "solver_type": solver_type,
            "solver": solver_folder,
            "display_name": f"{llm_name}{display_suffix}",
            "model": llm_name,
            "strategy": strat,
            "problem_id": p_id,
            "source_problem_id": source_problem_id,
            "source_noise_std": native_noise,
            "code_hash": code_hash,
            "target_dir": str(target_dir),
            "dim": dim,
            "noise_std": eval_noise,
            "mode": mode_enum if not is_noise_robustness else GenerationMode.EXPLICIT,
            "target_runs": self.n_runs,
            "runs_found": inspection.reusable_trials,
            "recorded_trials": inspection.recorded_trials,
            "reason": inspection.reason,
            "status": inspection.status,
            "median_error": inspection.median_error,
            "is_filtered": False,
        }

    # ── Workload Auditing ────────────────────────────────────────────────────────

    def audit_champions_workload(self, include_noise_robustness: bool = False) -> pd.DataFrame:
        """Audit LLM champion algorithms (evaluates native environments by default)."""
        champions_flat = self.champion_selection.flatten_champions()
        rows = [
            self._build_champion_audit_row(
                champ_key=k,
                champ=c,
                eval_noise=float(c.get("noise_std", 0.0)),
                is_noise_robustness=False,
            )
            for k, c in champions_flat.items()
        ]
        df = pd.DataFrame(rows)
        if include_noise_robustness:
            df_cross = self.audit_noise_robustness_workload()
            if not df_cross.empty:
                df = pd.concat([df, df_cross], ignore_index=True)
        return df

    def audit_noise_robustness_workload(self) -> pd.DataFrame:
        """Audit frozen clean champions on their original functions with added noise."""
        if not self.config.cross_eval_clean_champions:
            return pd.DataFrame()
        champions_flat = self.champion_selection.flatten_champions()
        target_conditions = self._discover_target_conditions()
        noisy_levels = sorted(list({float(c[1]) for c in target_conditions if c[1] > 0.0}))
        if not noisy_levels:
            return pd.DataFrame()

        rows = []
        for k, c in champions_flat.items():
            native_noise = float(c.get("noise_std", 0.0))
            is_clean = native_noise == 0.0 and c.get("mode") == GenerationMode.EXPLICIT
            if not is_clean:
                continue
            for n_std in noisy_levels:
                rows.append(
                    self._build_champion_audit_row(
                        champ_key=k,
                        champ=c,
                        eval_noise=n_std,
                        is_noise_robustness=True,
                    )
                )
        return pd.DataFrame(rows)

    def audit_cross_function_workload(self) -> pd.DataFrame:
        """Audit frozen baseline-strategy champions on each clean target function."""
        if not self.config.cross_function_enabled:
            return pd.DataFrame()
        rows = []
        for key, champion in self.champion_selection.flatten_champions().items():
            if (
                float(champion.get("noise_std", 0.0)) != 0.0
                or champion.get("mode") != GenerationMode.EXPLICIT
                or champion.get("prompt_strategy", "baseline") != "baseline"
            ):
                continue
            for target in sorted(
                set(self.config.cross_function_problem_ids) | {champion["problem_id"]}
            ):
                rows.append(
                    self._build_champion_audit_row(
                        key,
                        champion,
                        0.0,
                        False,
                        target_problem_id=target,
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
                inspection = self.inspect_status(
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
                        "mode": GenerationMode.EXPLICIT,
                        "target_runs": self.n_runs,
                        "runs_found": inspection.reusable_trials,
                        "recorded_trials": inspection.recorded_trials,
                        "reason": inspection.reason,
                        "status": inspection.status,
                        "median_error": inspection.median_error,
                        "is_filtered": False,
                    }
                )
        return pd.DataFrame(rows)

    def audit_workload(self, solver_type: str = "all") -> pd.DataFrame:
        """Audit native, noise-robustness, transfer, and classical workflows."""
        dfs = []
        if solver_type in ("all", "champions"):
            dfs.append(self.audit_champions_workload())
        if solver_type in ("all", "noise_robustness"):
            dfs.append(self.audit_noise_robustness_workload())
        if solver_type in ("all", "cross_function"):
            transfer = self.audit_cross_function_workload()
            dfs.append(transfer)
            if solver_type == "cross_function" and not transfer.empty:
                # Baselines are independent of the source champion: evaluate once
                # in their ordinary folders, then reuse for every source row.
                baselines = self.audit_baselines_workload()
                dfs.append(
                    baselines[
                        (baselines["noise_std"] == 0.0)
                        & baselines["dim"].isin(transfer["dim"])
                        & baselines["problem_id"].isin(transfer["problem_id"])
                    ]
                )
        if solver_type in ("all", "baselines"):
            dfs.append(self.audit_baselines_workload())

        if not dfs:
            return pd.DataFrame()
        return (
            pd.concat(dfs, ignore_index=True) if any(not df.empty for df in dfs) else pd.DataFrame()
        )
