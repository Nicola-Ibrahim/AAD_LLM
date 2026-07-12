from pathlib import Path
from typing import Any

from schema import ExperimentSummary
from storage.repository import ExperimentRepository
from storage.blob import CodeBlobSaver
from storage.mapper import build_experiment_summary


class ExperimentManager:
    """Facade orchestrating the persistence of code blobs and experiment metadata.

    Acts as the entry door/bouncer for the storage layer.
    """

    def __init__(self, store: ExperimentRepository, base_dir: str | Path = "experiments"):
        self.store = store
        self.base_dir = Path(base_dir)
        self.blob_saver = CodeBlobSaver(self.base_dir)

    def save_experiment(
        self,
        history: list[Any],
        problem: Any = None,
        dim: Any = None,
        mode: Any = None,
        llm_name: Any = None,
        **kwargs: Any,
    ) -> None:
        """Saves code blobs to the filesystem and persists metadata to the underlying store.

        Supports both the modern signature:
            save_experiment(history, problem: ProblemProfile, mode: str, llm_name: str)
        And the legacy/backward-compatible signature:
            save_experiment(history, problem_id: int, dim: int, mode: str, llm_name: str)
        """
        from schema import ProblemProfile

        # 1. Distinguish between signatures
        if isinstance(problem, ProblemProfile):
            actual_problem = problem
            actual_mode = mode
            actual_llm_name = llm_name
        else:
            problem_id = kwargs.get("problem_id", problem)
            actual_dim = kwargs.get("dim", dim)
            actual_mode = kwargs.get("mode", mode)
            actual_llm_name = kwargs.get("llm_name", llm_name)

            if problem_id is None or actual_dim is None:
                raise TypeError(
                    "save_experiment() missing required arguments. Expects either "
                    "(history, problem: ProblemProfile, mode, llm_name) or "
                    "(history, problem_id, dim, mode, llm_name)"
                )

            # Guess/fallback values for noise_std/true_optimum/instance_id
            noise_std = kwargs.get("noise_std", 0.0)
            if noise_std == 0.0 and actual_mode == "noisy":
                noise_std = 0.05  # Standard noisy mode standard deviation
            instance_id = kwargs.get("instance_id", 1)
            true_optimum = kwargs.get("true_optimum", 0.0)  # Standard optimum

            actual_problem = ProblemProfile(
                problem_id=problem_id,
                dim=actual_dim,
                noise_std=noise_std,
                instance_id=instance_id,
                true_optimum=true_optimum,
            )

        if actual_mode is None or actual_llm_name is None:
            raise TypeError(
                "save_experiment() missing required arguments: 'mode' and 'llm_name' must not be None."
            )

        # 2. Save code blobs (mutates history metadata in-place to add paths)
        self.blob_saver.save(history, actual_problem, actual_mode, actual_llm_name)

        # 3. Build the structured summary
        summary = build_experiment_summary(history, actual_problem, actual_mode, actual_llm_name)

        # 4. Persist to DB or JSON via the specific store
        self.store.save(summary)

    def load(
        self,
        problem_id: int | None = None,
        llm_name: str | None = None,
        dim: int | None = None,
        mode: str | None = None,
    ) -> list[ExperimentSummary]:
        """Loads and filters stored ExperimentSummary objects from the underlying store."""
        return self.store.load(
            problem_id=problem_id,
            llm_name=llm_name,
            dim=dim,
            mode=mode,
        )
