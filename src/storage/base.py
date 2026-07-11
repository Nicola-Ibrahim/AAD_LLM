from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path

from schema import ExperimentSummary, IterationMetadata


class ExperimentStore(ABC):
    """Abstract base class representing a storage backend for experiment results."""

    @property
    def base_dir(self) -> Path:
        """Returns the base directory for storing blobs (like source code). Defaults to 'experiments'."""
        return Path("experiments")

    def save_experiment(
        self,
        history: list[Any],
        problem_id: int,
        dim: int,
        mode: str,
        llm_name: str,
    ) -> None:
        """Extracts iteration metadata from the LLaMEA run history, compiles it, saves code blobs, and persists it."""

        # Determine blob directory for source code
        experiment_name = f"bbob_{problem_id}_dim{dim}_{mode}"
        code_dir = self.base_dir / "code" / llm_name / experiment_name
        code_dir.mkdir(parents=True, exist_ok=True)

        # Save code blobs
        for i, solution in enumerate(history):
            iteration_num = i + 1
            meta = getattr(solution, "metadata", None)
            if meta and hasattr(solution, "code") and solution.code:
                code_path = code_dir / f"iter_{iteration_num}.py"
                with open(code_path, "w", encoding="utf-8") as f:
                    f.write(solution.code)
                meta.code_path = str(code_path)

        summary = self._build_summary(history, problem_id, dim, mode, llm_name)
        self.save(summary)

    def _build_summary(
        self,
        history: list[Any],
        problem_id: int,
        dim: int,
        mode: str,
        llm_name: str,
    ) -> ExperimentSummary:
        """Assembles an ExperimentSummary model instance from raw run history."""
        iterations_data: list[IterationMetadata] = []

        best_iteration = None
        best_error = float("inf")
        best_algo = None

        for i, solution in enumerate(history):
            iteration_num = i + 1
            meta: IterationMetadata | None = getattr(solution, "metadata", None)

            if not meta:
                continue

            meta.iteration = iteration_num
            iterations_data.append(meta)

            if meta.final_error is not None and meta.final_error < best_error:
                best_error = meta.final_error
                best_iteration = iteration_num
                best_algo = meta.algorithm_name

        true_optimum = None
        noise_std = None
        if history and hasattr(history[0], "metadata") and history[0].metadata:
            true_optimum = history[0].metadata.true_optimum
            noise_std = history[0].metadata.noise_std

        best_err_val = best_error if best_error != float("inf") else None

        return ExperimentSummary(
            problem_id=problem_id,
            dim=dim,
            mode=mode,
            llm_name=llm_name,
            noise_std=noise_std,
            true_optimum=true_optimum,
            best_iteration=best_iteration,
            best_algorithm=best_algo,
            best_final_error=best_err_val,
            iterations=iterations_data,
        )

    @abstractmethod
    def save(self, summary: ExperimentSummary) -> None:
        """Persists a pre-built ExperimentSummary."""
        pass

    @abstractmethod
    def load(
        self,
        problem_id: int | None = None,
        llm_name: str | None = None,
        dim: int | None = None,
        mode: str | None = None,
    ) -> list[ExperimentSummary]:
        """Loads and filters stored ExperimentSummary objects."""
        pass

    @abstractmethod
    def print_table(self) -> None:
        """Prints a formatted ASCII comparison table of stored experiments."""
        pass
