import math
from datetime import datetime, timezone
from typing import Any

from pydantic import AliasChoices, Field, field_validator

from evolution.domain.base import DomainEntity, EntityID
from evolution.domain.enums import PromptStrategy, SynthesisMode
from evolution.domain.vos.iteration import IterationMetadata
from evolution.domain.vos.problem_profile import ProblemProfile


class ExperimentSummary(DomainEntity):
    """Aggregated result of a full LLaMEA evolution run."""

    id: EntityID | None = Field(
        default=None,
        description="Globally unique experiment primary key.",
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
        examples=[1000, 10000],
    )
    max_iterations: int | None = Field(
        default=None,
        description="Maximum synthesis iterations set for the experiment run.",
        examples=[10, 20],
    )
    status: str = Field(
        default="running",
        description="Current lifecycle status of the experiment: running, completed, or failed.",
        examples=["completed", "running", "failed"],
    )
    started_at: str | None = Field(
        default=None,
        description="ISO timestamp string when the experiment execution started.",
        examples=["2026-08-02T10:00:00+00:00", None],
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
    )
    iterations: list[IterationMetadata] = Field(
        default_factory=list,
        description="List of individual iteration metadata records.",
    )

    @field_validator("best_final_error", mode="before")
    @classmethod
    def sanitize_best_error(cls, v: Any) -> Any:
        if isinstance(v, float) and (math.isinf(v) or math.isnan(v)):
            return None
        return v

    @property
    def experiment_id(self) -> int | None:
        """Property alias for experiment primary key ID."""
        return self.id

    @classmethod
    def new(
        cls,
        experiment_id: int,
        problem: ProblemProfile,
        mode: SynthesisMode,
        llm_name: str,
        prompt_strategy: PromptStrategy = PromptStrategy.BASELINE,
        budget: int | None = None,
        max_iterations: int | None = None,
        started_at: str | None = None,
    ) -> "ExperimentSummary":
        """Factory to initialize a new active ExperimentSummary aggregate."""
        return cls(
            id=experiment_id,
            mode=mode,
            llm_name=llm_name,
            prompt_strategy=prompt_strategy,
            budget=budget,
            max_iterations=max_iterations,
            status="running",
            started_at=started_at or datetime.now(timezone.utc).isoformat(),
            problem=problem,
            iterations=[],
        )

    def record_iteration(
        self,
        meta: IterationMetadata,
        iteration_num: int | None = None,
    ) -> None:
        """Records an iteration result and updates champion metrics if performance improved."""
        self.iterations.append(meta)
        it_idx = (
            iteration_num
            if iteration_num is not None
            else (meta.iteration or len(self.iterations))
        )
        err = meta.fitness.final_error
        if err is not None and math.isfinite(err):
            if self.best_final_error is None or err < self.best_final_error:
                self.best_final_error = err
                self.best_algorithm = meta.algorithm_name
                self.best_iteration = it_idx

    def complete(self) -> None:
        """Transitions experiment lifecycle to completed and records finish timestamp."""
        self.status = "completed"
        self.finished_at = datetime.now(timezone.utc).isoformat()

    def fail(self) -> None:
        """Transitions experiment lifecycle to failed and records finish timestamp."""
        self.status = "failed"
        self.finished_at = datetime.now(timezone.utc).isoformat()
