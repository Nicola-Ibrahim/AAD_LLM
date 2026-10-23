"""Discover executable conditions and project the same work into audit tables."""

import hashlib
from pathlib import Path

import pandas as pd

from benchmarking.application.benchmark.models import BenchmarkTask
from benchmarking.application.benchmark_config import BenchmarkConfig
from benchmarking.application.champions import Champion, GenerationMode
from benchmarking.application.interfaces.benchmark_state_store import BenchmarkStateStore
from benchmarking.application.interfaces.candidate_code_reader import CandidateCodeReader
from benchmarking.application.interfaces.synthesis_read_repository import SynthesisReadRepository
from benchmarking.application.select_champions import ChampionSelectionService
from benchmarking.domain.services.condition_status import ConditionStatus, inspect_condition
from benchmarking.domain.services.resolvers import ModelNames
from shared.application.interfaces.candidate_executor import CANDIDATE_EXECUTION_VERSION


class BenchmarkWorkload:
    """Load one champion selection per discovery; audits never drive execution."""

    def __init__(
        self,
        sqlite_repo: SynthesisReadRepository,
        champion_selection: ChampionSelectionService,
        state_repo: BenchmarkStateStore,
        code_reader: CandidateCodeReader,
        model_names: ModelNames,
        config: BenchmarkConfig,
        planned_target_conditions: tuple[tuple[int, float, int], ...] = (),
    ) -> None:
        self.sqlite_repo = sqlite_repo
        self.champion_selection = champion_selection
        self.state_repo = state_repo
        self.code_reader = code_reader
        self.model_names = model_names
        self.config = config
        self.planned_target_conditions = planned_target_conditions

    def _discover_target_conditions(
        self, champions: dict[str, Champion]
    ) -> list[tuple[int, float, int]]:
        raw_conditions = self.sqlite_repo.get_target_conditions()
        if not raw_conditions:
            raw_conditions = [
                (c["dim"], c.get("noise_std", 0.0), c["problem_id"]) for c in champions.values()
            ]
        if not raw_conditions:
            raw_conditions = list(self.planned_target_conditions)

        # Keep observed tuples, not a Cartesian product that invents conditions.
        conditions = set(raw_conditions)
        if self.config.target_noise_stds:
            conditions = {c for c in conditions if c[1] in self.config.target_noise_stds}
        if self.config.cross_function_enabled:
            conditions.update(
                (dim, 0.0, problem)
                for dim in {c[0] for c in raw_conditions}
                for problem in self.config.cross_function_problem_ids
            )
        return sorted(conditions)

    def inspect_status(
        self,
        target_dir: Path,
        expected_code_hash: str | None = None,
        code_valid: bool = True,
        *,
        champion: bool = False,
    ) -> ConditionStatus:
        return inspect_condition(
            code_available=code_valid,
            directory_exists=self.state_repo.solver_directory_exists(target_dir),
            provenance=self.state_repo.read_provenance(target_dir),
            expected_code_hash=expected_code_hash,
            expected_trials=self.config.trials_per_condition,
            expected_budget=self.config.budget,
            trial_schedule=self.config.trial_schedule,
            expected_execution_version=CANDIDATE_EXECUTION_VERSION if champion else None,
        )

    def _champion_task(
        self,
        key: str,
        champion: Champion,
        noise_std: float,
        *,
        noise_robustness: bool = False,
        target_problem_id: int | None = None,
    ) -> BenchmarkTask:
        source_problem = champion["problem_id"]
        problem = source_problem if target_problem_id is None else target_problem_id
        dim = champion["dim"]
        strategy = champion.get("prompt_strategy", "baseline")
        model = champion.get("llm_name", "llamea")
        slug = self.model_names.get_model_slug(model)
        native_noise = champion.get("noise_std", 0.0)
        mode = GenerationMode(
            champion.get("mode") or ("implicit" if "_implicit" in key else "explicit")
        )
        suffix = (
            "_implicit" if mode == GenerationMode.IMPLICIT else "_noisy" if native_noise else ""
        )
        solver = f"{slug}_{strategy}{suffix}"
        code_path = Path(champion["code_path"])
        code_available = self.code_reader.exists(code_path)
        code_hash = (
            hashlib.sha256(self.code_reader.read(code_path).strip().encode("utf-8")).hexdigest()
            if code_available
            else None
        )
        directory = self.state_repo.condition_directory(dim, noise_std, problem, solver)
        if target_problem_id is not None and problem != source_problem:
            directory = self.state_repo.transfer_directory(
                source_problem, dim, noise_std, problem, solver, code_hash or "missing"
            )
        solver_type = "noise_robustness" if noise_robustness else "champion"
        row_key = f"{key}_eval_std{noise_std}" if noise_robustness else key
        display_suffix = " (noise robustness)" if noise_robustness else ""
        if target_problem_id is not None:
            solver_type = "cross_function"
            row_key = f"{key}_target_f{problem}"
            display_suffix = f" (f{source_problem} → f{problem})"
        return BenchmarkTask(
            key=row_key,
            raw_key=key,
            solver_type=solver_type,
            solver=solver,
            display_name=f"{model}{display_suffix}",
            model=model,
            strategy=strategy,
            problem_id=problem,
            dim=dim,
            noise_std=noise_std,
            mode=GenerationMode.EXPLICIT if noise_robustness else mode,
            target_dir=directory,
            inspection=self.inspect_status(directory, code_hash, code_available, champion=True),
            champion=champion,
            code_hash=code_hash,
        )

    def _baseline_tasks(self, conditions: list[tuple[int, float, int]]) -> list[BenchmarkTask]:
        tasks = []
        for solver in self.config.classical_baselines:
            for dim, noise, problem in conditions:
                directory = self.state_repo.condition_directory(dim, noise, problem, solver)
                key = f"f{problem}_{dim}D_std{noise}_{solver}"
                tasks.append(
                    BenchmarkTask(
                        key=key,
                        raw_key=key,
                        solver_type="baseline",
                        solver=solver,
                        display_name=self.config.baseline_labels.get(solver, solver.upper()),
                        model=solver,
                        strategy="classical",
                        problem_id=problem,
                        dim=dim,
                        noise_std=noise,
                        mode=GenerationMode.EXPLICIT,
                        target_dir=directory,
                        inspection=self.inspect_status(directory),
                        champion=None,
                        code_hash=None,
                    )
                )
        return tasks

    def discover(self, solver_type: str = "all") -> list[BenchmarkTask]:
        """Return typed tasks with exact candidates, in the existing execution order."""
        allowed = {"all", "champions", "noise_robustness", "cross_function", "baselines"}
        if solver_type not in allowed:
            raise ValueError(f"Unknown benchmark workflow: {solver_type}")
        champions = self.champion_selection.flatten_champions()
        tasks = []
        if solver_type in {"all", "champions"}:
            tasks.extend(
                self._champion_task(key, c, c.get("noise_std", 0.0)) for key, c in champions.items()
            )
        if solver_type in {"all", "noise_robustness"} and self.config.noise_robustness_enabled:
            conditions = self._discover_target_conditions(champions)
            levels = sorted(
                {n for n in self.config.target_noise_stds if n > 0.0}
                if self.config.target_noise_stds
                else {n for _, n, _ in conditions if n > 0.0}
            )
            tasks.extend(
                self._champion_task(key, c, noise, noise_robustness=True)
                for key, c in champions.items()
                if c.get("noise_std", 0.0) == 0.0 and c.get("mode") == GenerationMode.EXPLICIT
                for noise in levels
            )
        if solver_type in {"all", "cross_function"} and self.config.cross_function_enabled:
            transfer = [
                self._champion_task(key, c, 0.0, target_problem_id=target)
                for key, c in champions.items()
                if c.get("noise_std", 0.0) == 0.0
                and c.get("mode") == GenerationMode.EXPLICIT
                and c.get("prompt_strategy", "baseline") == "baseline"
                for target in sorted(
                    set(self.config.cross_function_problem_ids) | {c["problem_id"]}
                )
            ]
            tasks.extend(transfer)
            if solver_type == "cross_function" and transfer:
                dims = {task.dim for task in transfer}
                problems = {task.problem_id for task in transfer}
                tasks.extend(
                    self._baseline_tasks(
                        [
                            c
                            for c in self._discover_target_conditions(champions)
                            if c[1] == 0.0 and c[0] in dims and c[2] in problems
                        ]
                    )
                )
        if solver_type in {"all", "baselines"}:
            tasks.extend(self._baseline_tasks(self._discover_target_conditions(champions)))
        return tasks

    def audit_workload(self, solver_type: str = "all") -> pd.DataFrame:
        """Read-only presentation of the same tasks used for execution."""
        return pd.DataFrame(task.audit_row() for task in self.discover(solver_type))

    def audit_champions_workload(self, include_noise_robustness: bool = False) -> pd.DataFrame:
        tasks = self.discover("champions")
        if include_noise_robustness:
            tasks.extend(self.discover("noise_robustness"))
        return pd.DataFrame(task.audit_row() for task in tasks)

    def audit_noise_robustness_workload(self) -> pd.DataFrame:
        return self.audit_workload("noise_robustness")

    def audit_cross_function_workload(self) -> pd.DataFrame:
        return pd.DataFrame(
            task.audit_row()
            for task in self.discover("cross_function")
            if task.solver_type == "cross_function"
        )

    def audit_baselines_workload(self) -> pd.DataFrame:
        return self.audit_workload("baselines")
