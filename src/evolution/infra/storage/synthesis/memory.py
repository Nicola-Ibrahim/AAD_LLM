"""Process-local experiment storage for synthesis that must not persist a study."""

from evolution.domain.entities import Experiment
from evolution.domain.enums import PromptStrategy, SynthesisMode
from evolution.domain.interfaces.synthesis_repository import SynthesisRepository
from evolution.domain.vos import IterationMetadata, ProblemProfile


class MemorySynthesisRepository(SynthesisRepository):
    """Retain real experiment state only for the lifetime of this repository."""

    def __init__(self) -> None:
        self.experiments: dict[int, Experiment] = {}
        self._next_id = 1

    def create_experiment(
        self,
        problem: ProblemProfile,
        mode: SynthesisMode,
        llm_name: str,
        prompt_strategy: PromptStrategy = PromptStrategy.BASELINE,
        *,
        budget: int,
        max_iterations: int,
        synthesis_seed: int | None = None,
    ) -> int:
        experiment = Experiment(
            id=self._next_id,
            problem=problem,
            mode=mode,
            llm_name=llm_name,
            prompt_strategy=prompt_strategy,
            budget=budget,
            max_iterations=max_iterations,
            synthesis_seed=synthesis_seed,
        )
        self.experiments[experiment.id] = experiment
        self._next_id += 1
        return experiment.id

    def load(
        self,
        *,
        experiment_id: int | None = None,
        problem_id: int | None = None,
        instance_id: int | None = None,
        llm_name: str | None = None,
        mode: SynthesisMode | None = None,
        prompt_strategy: PromptStrategy | None = None,
        noise_std: float | None = None,
        dim: int | None = None,
        status: str | None = None,
    ) -> list[Experiment]:
        filters = {
            "id": experiment_id,
            "llm_name": llm_name,
            "mode": mode,
            "prompt_strategy": prompt_strategy,
            "status": status,
        }
        problem_filters = {
            "problem_id": problem_id,
            "instance_id": instance_id,
            "noise_std": noise_std,
            "dim": dim,
        }
        return [
            exp.model_copy(deep=True)
            for exp in self.experiments.values()
            if all(value is None or getattr(exp, key) == value for key, value in filters.items())
            and all(
                value is None or getattr(exp.problem, key) == value
                for key, value in problem_filters.items()
            )
        ]

    def load_by_ids(self, experiment_ids: list[int]) -> list[Experiment]:
        return [
            self.experiments[key].model_copy(deep=True)
            for key in experiment_ids
            if key in self.experiments
        ]

    def get_experiment_status(self, experiment_id: int) -> tuple[str | None, int]:
        experiment = self.experiments.get(experiment_id)
        return (experiment.status.value, len(experiment.iterations)) if experiment else (None, 0)

    def append_iteration(self, experiment_id: int, metadata: IterationMetadata) -> None:
        self.experiments[experiment_id].record_iteration(metadata.model_copy(deep=True))

    def save_experiment(self, exp: Experiment) -> None:
        self.experiments[exp.id] = exp.model_copy(deep=True)

    def mark_failed(self, experiment_id: int, reason: str = "") -> None:
        self.experiments[experiment_id].fail()

    def reset_experiment(self, experiment_id: int) -> None:
        old = self.experiments[experiment_id]
        self.experiments[experiment_id] = Experiment(
            id=old.id,
            problem=old.problem,
            mode=old.mode,
            llm_name=old.llm_name,
            prompt_strategy=old.prompt_strategy,
            budget=old.budget,
            max_iterations=old.max_iterations,
            synthesis_seed=old.synthesis_seed,
        )
