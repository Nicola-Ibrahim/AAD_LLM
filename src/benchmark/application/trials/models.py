"""Typed work items passed from discovery to execution and audit presentation."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from benchmark.application.champions import Champion, GenerationMode
from benchmark.domain.benchmark_results import executed_trial_count
from benchmark.domain.services.condition_status import ConditionStatus
from benchmark.domain.trial_schedule import TrialIdentity
from shared.application.interfaces.candidate_executor import CandidateExecutor
from shared.domain.problem import BaseProblem

SolverType = Literal["champion", "noise_robustness", "cross_function", "baseline"]
BaselineRunner = Callable[[BaseProblem, int], tuple[float, float, int]]
BaselineRunnerResolver = Callable[[str], BaselineRunner]
ExecutorBuilder = Callable[[float], CandidateExecutor]


@dataclass(frozen=True, slots=True)
class RecordedTrial:
    """One terminal outcome, including its diagnostics and associated search trace."""

    instance_id: int
    seed: int
    true_optimum: float
    best_objective: float
    error: float
    runtime: float
    evaluations_used: int
    trace_run_index: int | None
    observations: list[dict[str, float | int]]
    error_type: str | None
    error_message: str | None
    error_traceback: str | None

    @property
    def identity(self) -> TrialIdentity:
        return self.instance_id, self.seed

    def provenance_row(self, trial_number: int) -> dict[str, object]:
        return {
            "trial": trial_number,
            "instance_id": self.instance_id,
            "seed": self.seed,
            "true_optimum": self.true_optimum,
            "best_objective": self.best_objective,
            "error": self.error,
            "evaluations_used": self.evaluations_used,
            "trace_run_index": self.trace_run_index,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "error_traceback": self.error_traceback,
        }

    @classmethod
    def from_provenance(cls, provenance: dict[str, object]) -> list["RecordedTrial"]:
        """Restore historical parallel columns once, keeping optional sidecars aligned."""
        count = executed_trial_count(provenance)
        if any(len(provenance.get(key, [])) < count for key in ("instance_ids", "trial_seeds")):
            raise ValueError(
                "Cannot safely resume: recorded trials lack instance/seed identities. "
                "Existing results have not been removed."
            )
        rows = provenance.get("trial_records", [])
        observations = provenance.get("observed_objectives", [])
        trials = []
        for index in range(count):
            row = rows[index] if index < len(rows) else {}
            trials.append(
                cls(
                    instance_id=provenance["instance_ids"][index],
                    seed=provenance["trial_seeds"][index],
                    true_optimum=provenance["true_optima"][index],
                    best_objective=provenance["best_objectives"][index],
                    error=provenance["clean_errors"][index],
                    runtime=provenance["runtimes"][index],
                    evaluations_used=provenance["evaluations_used"][index],
                    trace_run_index=row.get("trace_run_index"),
                    observations=observations[index] if index < len(observations) else [],
                    error_type=row.get("error_type"),
                    error_message=row.get("error_message"),
                    error_traceback=row.get("error_traceback"),
                )
            )
        return trials


@dataclass(frozen=True, slots=True)
class BenchmarkTask:
    """One condition and its exact candidate; baselines have no champion."""

    key: str
    raw_key: str
    solver_type: SolverType
    solver: str
    display_name: str
    model: str
    strategy: str
    problem_id: int
    dim: int
    noise_std: float
    mode: GenerationMode
    target_dir: Path
    inspection: ConditionStatus
    champion: Champion | None
    code_hash: str | None

    def audit_row(self) -> dict[str, object]:
        """Project the task into the existing notebook-facing table schema."""
        row = {
            "key": self.key,
            "solver_type": self.solver_type,
            "solver": self.solver,
            "display_name": self.display_name,
            "model": self.model,
            "strategy": self.strategy,
            "problem_id": self.problem_id,
            "dim": self.dim,
            "noise_std": self.noise_std,
            "mode": self.mode,
            "target_runs": self.inspection.expected_trials,
            "runs_found": self.inspection.reusable_trials,
            "recorded_trials": self.inspection.recorded_trials,
            "reason": self.inspection.reason,
            "status": self.inspection.status,
            "median_error": self.inspection.median_error,
            "is_filtered": False,
        }
        if self.champion is not None:
            row.update(
                raw_key=self.raw_key,
                source_problem_id=self.champion["problem_id"],
                source_noise_std=self.champion.get("noise_std", 0.0),
                code_hash=self.code_hash,
                target_dir=str(self.target_dir),
            )
        return row
