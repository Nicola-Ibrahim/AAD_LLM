import math
from datetime import datetime, timezone

from pydantic import AliasChoices, ConfigDict, Field, field_validator

from evolution.domain.base import DomainEntity, EntityID
from evolution.domain.enums import PromptStrategy, SynthesisMode
from evolution.domain.enums.experiment_status import ExperimentStatus
from evolution.domain.vos.iteration import IterationMetadata
from evolution.domain.vos.problem_profile import ProblemProfile


class Experiment(DomainEntity):
    """Synthesis measurements and lifecycle; benchmarking owns independent analysis."""

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    id: EntityID = Field(
        frozen=True,
        description="Globally unique experiment primary key.",
        gt=0,
        validation_alias=AliasChoices("id", "experiment_id"),
    )
    mode: SynthesisMode = Field(description="Experiment running mode.")
    llm_name: str = Field(
        description="Name of the LLM used to generate algorithm candidates.",
        examples=["qwen2.5-coder-7b-instruct-q4_k_m", "gpt-4o-mini"],
    )
    prompt_strategy: PromptStrategy = Field(
        default=PromptStrategy.BASELINE,
        description="Name of the prompt strategy used for algorithm synthesis.",
    )
    budget: int | None = Field(
        default=None,
        description="Evaluation budget allocated per candidate algorithm run.",
        gt=0,
        examples=[1000, 10000],
    )
    max_iterations: int | None = Field(
        default=None,
        description="Maximum synthesis iterations set for the experiment run.",
        gt=0,
        examples=[10, 20],
    )
    synthesis_seed: int | None = Field(
        default=None,
        description="Seed assigned to this independent synthesis replicate.",
    )
    status: ExperimentStatus = Field(
        default=ExperimentStatus.RUNNING,
        frozen=True,
        description="Current lifecycle status of the experiment: running, completed, or failed.",
        examples=["completed", "running", "failed"],
    )
    started_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp string when the experiment execution started.",
        examples=["2026-08-02T10:00:00+00:00"],
    )
    finished_at: str | None = Field(
        default=None,
        description="ISO timestamp string when the experiment execution finished.",
        examples=["2026-08-02T10:15:00+00:00", None],
    )
    problem: ProblemProfile = Field(
        description="Configuration of the BBOB problem for this execution run."
    )
    best_iteration: int | None = Field(
        default=None,
        description="The 1-based iteration index that produced the minimum final error.",
        gt=0,
        examples=[8, None],
    )
    best_algorithm: str | None = Field(
        default=None,
        description="Name of the best-performing algorithm iteration.",
        examples=["NoisyHillClimber", None],
    )
    best_final_error: float | None = Field(
        default=None,
        description="The minimum final error achieved across all iterations in this run.",
        examples=[0.0001, None],
        ge=0,
    )
    iterations: list[IterationMetadata] = Field(
        default_factory=list,
        description="List of individual iteration metadata records.",
    )

    @field_validator("best_final_error", mode="before")
    @classmethod
    def sanitize_best_error(cls, v: float | None) -> float | None:
        if isinstance(v, float) and (math.isinf(v) or math.isnan(v)):
            return None
        return v

    @property
    def experiment_id(self) -> int:
        """Property alias for experiment primary key ID."""
        return self.id

    def record_iteration(
        self,
        meta: IterationMetadata,
    ) -> None:
        """Records an iteration result and updates champion metrics if performance improved."""
        if self.status != ExperimentStatus.RUNNING:
            raise ValueError("Only a running experiment can record candidates")
        self.iterations.append(meta)
        it_idx = meta.iteration if meta.iteration is not None else len(self.iterations)
        err = meta.fitness.final_error
        if err is not None and math.isfinite(err):
            if self.best_final_error is None or err < self.best_final_error:
                self.best_final_error = err
                self.best_algorithm = meta.algorithm_name
                self.best_iteration = it_idx

    @property
    def incumbent(self) -> IterationMetadata | None:
        """Lowest finite synthesis error; exact ties retain generation order.

        Benchmark champion selection independently applies its evaluation-count
        tie-break across synthesis records. This property preserves LLaMEA's
        synthesis incumbent, rather than introducing that benchmark tie-break.
        """
        return min(
            (
                item
                for item in self.iterations
                if item.fitness.final_error is not None and math.isfinite(item.fitness.final_error)
            ),
            key=lambda item: item.fitness.final_error,
            default=None,
        )

    def complete(self) -> None:
        """Complete a running experiment; repeated completion is idempotent."""
        if self.status == ExperimentStatus.COMPLETED:
            return
        if self.status != ExperimentStatus.RUNNING:
            raise ValueError("A failed experiment must be explicitly restarted before completion")
        object.__setattr__(self, "status", ExperimentStatus.COMPLETED)
        self.finished_at = datetime.now(timezone.utc).isoformat()

    def fail(self) -> None:
        """Fail a running experiment; repeated failure is idempotent."""
        if self.status == ExperimentStatus.FAILED:
            return
        if self.status != ExperimentStatus.RUNNING:
            raise ValueError("A completed experiment cannot fail during synthesis")
        object.__setattr__(self, "status", ExperimentStatus.FAILED)
        self.finished_at = datetime.now(timezone.utc).isoformat()
