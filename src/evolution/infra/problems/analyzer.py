"""IOH Analyzer Telemetry Component for BBOB Benchmark Experiments."""

from pathlib import Path
from types import TracebackType
from typing import Any

import ioh

from shared.config import DATA_DIR
from evolution.domain.interfaces import BaseProblem


class ProblemAnalyzer:
    """Context manager and telemetry service that encapsulates IOH Analyzer lifecycle.

    Attaches an `ioh.logger.Analyzer` to a `BaseProblem` instance, records improvement
    evaluations to disk, and guarantees safe flushing and closing upon context exit.

    Example:
        problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy())
        with ProblemAnalyzer(problem, algorithm_name="CMA-ES", folder_name="cmaes"):
            run_cmaes(problem, dim=2, budget=500)
    """

    def __init__(
        self,
        problem: BaseProblem,
        algorithm_name: str = "Algorithm",
        folder_name: str | None = None,
        log_dir: str | Path | None = None,
        algorithm_info: str = "algorithm_info",
        store_positions: bool = False,
    ):
        self.problem = problem
        self.algorithm_name = algorithm_name
        self.folder_name = (
            folder_name
            if folder_name is not None
            else f"run_{algorithm_name.lower().replace(' ', '_')}"
        )
        self.log_dir = (
            Path(log_dir)
            if log_dir is not None
            else DATA_DIR
            / "ioh_logs"
            / f"{problem.dim}D"
            / f"std_{problem.noise_std}"
            / f"f{problem.problem_id}"
        )
        self.algorithm_info = algorithm_info
        self.store_positions = store_positions

        self._logger: ioh.logger.Analyzer | None = None
        self._triggers: list[Any] | None = None

    @property
    def logger(self) -> ioh.logger.Analyzer | None:
        """Return the underlying IOH Analyzer logger instance if attached."""
        return self._logger

    def attach(self) -> "ProblemAnalyzer":
        """Instantiate and attach the IOH Analyzer to the problem."""
        if self._logger is not None:
            return self

        try:
            self._triggers = [ioh.logger.trigger.OnImprovement()]
            self._logger = ioh.logger.Analyzer(
                triggers=self._triggers,
                root=str(self.log_dir),
                folder_name=self.folder_name,
                algorithm_name=self.algorithm_name,
                algorithm_info=self.algorithm_info,
                store_positions=self.store_positions,
            )
            if hasattr(self.problem, "attach_logger"):
                self.problem.attach_logger(self._logger)
            elif hasattr(self.problem, "clean_problem"):
                self.problem.clean_problem.attach_logger(self._logger)
            elif hasattr(self.problem, "_clean_problem"):
                getattr(self.problem, "_clean_problem").attach_logger(self._logger)
        except Exception as e:
            print(f"[!] Could not attach IOH Analyzer: {e}")
            self._logger = None
            self._triggers = None

        return self

    def close(self) -> None:
        """Safely flush and close the IOH Analyzer logger."""
        if self._logger is not None:
            try:
                self._logger.close()
            except Exception:
                pass
            self._logger = None
            self._triggers = None

    def __enter__(self) -> "ProblemAnalyzer":
        self.attach()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()
