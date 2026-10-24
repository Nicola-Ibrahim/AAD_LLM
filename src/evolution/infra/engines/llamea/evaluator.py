"""LLaMEA Evaluation Adapter (Infrastructure Component).

Adapts the CandidateEvaluationService service to the LLaMEA Solution callable interface:
- Receives candidate solution from LLaMEA framework.
- Delegates code execution, bounds validation, scoring, and failure classification to CandidateEvaluationService.
- Sets fitness and feedback scores onto the LLaMEA Solution.
- Handles dual-repository persistence (filesystem code storage and database iteration telemetry).
- Manages state serialization for picklable warm starts.
"""

from llamea import Solution

from evolution.application.interfaces.code_store import SynthesisCodeStore
from evolution.application.interfaces.logger import BaseLogger
from evolution.application.synthesis.evaluate_candidate import CandidateEvaluationService
from evolution.application.synthesis.models import SessionConfig
from evolution.domain.entities import ExperimentSummary
from evolution.domain.interfaces.synthesis_repository import SynthesisRepository
from evolution.domain.vos import IterationMetadata, ProblemProfile
from evolution.infra.engines.llamea.prompts import FeedbackRenderer
from evolution.infra.logging import SynthesisLogger
from shared.application.interfaces.candidate_executor import CANDIDATE_EXECUTION_VERSION
from shared.domain.problem import BaseProblem
from shared.infra.execution.candidate_executor import create_candidate_executor


class Evaluator:
    """LLaMEA-compatible evaluator adapter for optimization problems.

    Acts as an infrastructure adapter delegating candidate evaluation to
    CandidateEvaluationService while fulfilling LLaMEA's callable contract.
    """

    def __init__(
        self,
        problem: BaseProblem,
        db_repo: SynthesisRepository,
        code_repo: SynthesisCodeStore,
        experiment_id: int,
        config: SessionConfig,
        candidate_evaluation_service: CandidateEvaluationService,
        initial_iteration: int = 0,
    ) -> None:
        self._problem = problem
        self._db_repo = db_repo
        self._code_repo = code_repo
        self._config = config
        self._experiment_id = experiment_id
        self._current_iteration = initial_iteration
        self._logger: BaseLogger = SynthesisLogger()
        self._experiment: ExperimentSummary | None = None
        self._candidate_evaluation_service = candidate_evaluation_service
        self._feedback_renderer = FeedbackRenderer()
        self._execution_contract = CANDIDATE_EXECUTION_VERSION

    @property
    def logger(self) -> BaseLogger:
        return self._logger

    @logger.setter
    def logger(self, value: BaseLogger) -> None:
        self._logger = value

    @property
    def experiment(self) -> ExperimentSummary | None:
        return self._experiment

    @experiment.setter
    def experiment(self, value: ExperimentSummary | None) -> None:
        self._experiment = value

    @property
    def problem_profile(self) -> ProblemProfile:
        return ProblemProfile(
            problem_id=self._problem.problem_id,
            dim=self._problem.dim,
            noise_std=self._problem.noise_std,
            noise_model=self._problem.noise_model,
            instance_id=self._problem.instance_id,
            true_optimum=self._problem.true_optimum,
        )

    def _persist_iteration(self, solution: Solution, metadata: IterationMetadata) -> None:
        """Record iteration count, save code file, and persist metadata to database repo."""
        self._current_iteration += 1
        code_path_str: str | None = None

        if self._code_repo is not None and solution.code:
            code_path = self._code_repo.save_code(
                code=solution.code,
                iteration_num=self._current_iteration,
                experiment_id=self._experiment_id,
            )
            code_path_str = str(code_path)

        updated_code = metadata.code.model_copy(update={"code_path": code_path_str})
        final_metadata = metadata.model_copy(
            update={
                "iteration": self._current_iteration,
                "code": updated_code,
            }
        )

        if self._db_repo is not None:
            self._db_repo.append_iteration(
                experiment_id=self._experiment_id,
                metadata=final_metadata,
            )

        if self._experiment is not None:
            self._experiment.record_iteration(final_metadata, self._current_iteration)

    def __call__(self, solution: Solution, explogger: object | None = None) -> Solution:
        """Execute and score a candidate optimization algorithm solution.

        Args:
            solution: The LLaMEA candidate solution containing its source code and name.
            explogger: Framework-level experiment logger, by default None.

        Returns:
            Solution: The modified solution object populated with fitness scores and feedback.
        """
        llm_gen_time = solution.metadata.get("llm_generation_time")
        result = self._candidate_evaluation_service.evaluate(
            code=solution.code,
            name=solution.name,
            llm_generation_time=llm_gen_time,
        )

        feedback = self._feedback_renderer.render(result, problem=self._problem)
        solution.set_scores(result.fitness_score, feedback)
        self._persist_iteration(solution, result.metadata)

        if self._logger is not None:
            if result.is_stagnated:
                self._logger.stagnation_warning(
                    self._config.stagnation_threshold, self._config.stagnation_threshold
                )
            succeeded = not result.is_failure and result.final_error is not None
            failure_reason = result.metadata.error.error_type if result.metadata.error else None
            self._logger.generation(
                gen_idx=self._current_iteration,
                total_gens=self._config.iterations,
                algo_name=solution.name or "Candidate",
                error=result.final_error if succeeded else None,
                fitness=result.fitness_score if succeeded else None,
                evals_used=result.metadata.execution.evaluations_used,
                runtime=result.metadata.execution.runtime_seconds,
                is_failure=not succeeded,
                failure_reason="" if succeeded else failure_reason or "ExecutionFailure",
            )

        return solution

    def __getstate__(self) -> dict[str, object]:
        state = self.__dict__.copy()
        state["_candidate_evaluation_service"] = None
        state["_logger"] = None
        return state

    def __setstate__(self, state: dict[str, object]) -> None:
        self.__dict__.update(state)
        self._logger = getattr(self, "_logger", None) or SynthesisLogger()
        self._feedback_renderer = getattr(self, "_feedback_renderer", None) or FeedbackRenderer()
        self._candidate_evaluation_service = CandidateEvaluationService(
            problem=self._problem,
            budget=self._config.budget,
            timeout_seconds=self._config.timeout_seconds,
            stagnation_threshold=self._config.stagnation_threshold,
            convergence_threshold=self._config.convergence_threshold,
            executor=create_candidate_executor(self._config.timeout_seconds),
        )
        if getattr(self, "_db_repo", None) is None:
            print(
                "[WARN] Evaluator resumed from pickle with _db_repo=None. "
                "Iteration persistence is DISABLED for this run. "
                "Call evaluator._db_repo = repo to re-attach."
            )
        if getattr(self, "_code_repo", None) is None:
            print(
                "[WARN] Evaluator resumed from pickle with _code_repo=None. "
                "Code file saving is DISABLED for this run."
            )
