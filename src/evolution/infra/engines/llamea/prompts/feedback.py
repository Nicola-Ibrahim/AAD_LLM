"""Feedback prompt templates and renderer for evolutionary algorithm synthesis.

Decouples natural language feedback prompt generation from domain evaluation logic.
Provides structured templates and a FeedbackRenderer that formats evaluation results
into actionable diagnostic prompts for LLM-driven algorithm generation.
"""

from evolution.domain.interfaces.problem import BaseProblem
from evolution.domain.vos.evaluation_result import AlgorithmEvaluationResult

META_FEEDBACK_DIVERSITY_INJECTION = (
    "\n\n[META-FEEDBACK]\n\n"
    "The last several generated algorithms failed to execute correctly.\n\n"
    "Try a substantially different search mechanism rather than making only minor modifications to the previous approach.\n\n"
    "Check the previous implementation for the source of the failure and ensure that the new algorithm respects the objective interface, search bounds, evaluation budget, and numerical constraints."
)

TIMEOUT_FEEDBACK_TEMPLATE = (
    "[TIMEOUT]\n\n"
    "The generated algorithm exceeded the execution time limit.\n\n"
    "Reduce unnecessary computation and ensure that the implementation can complete within the available execution time and evaluation budget."
)

RUNTIME_ERROR_FEEDBACK_TEMPLATE = (
    "[RUNTIME ERROR]\n\n"
    "The generated algorithm failed during execution.\n\n"
    "Error:\n{error_str}"
    "{code_section}\n\n"
    "Fix the cause of the failure in the next candidate.\n\n"
    "Ensure that:\n"
    "- array shapes and dimensions are valid;\n"
    "- numerical operations are well-defined;\n"
    "- all variables are initialized before use;\n"
    "- the search stays within the provided bounds;\n"
    "- every objective evaluation is counted;\n"
    "- the total number of objective evaluations does not exceed the budget."
)

SUCCESS_CLEAN_FEEDBACK_TEMPLATE = (
    "[RESULT]\n\n"
    "The generated algorithm executed successfully.\n\n"
    "Final objective error:\n{err_str}\n\n"
    "Use this result together with the previous algorithm history when designing the next candidate."
)

SUCCESS_NOISY_FEEDBACK_TEMPLATE = (
    "[RESULT]\n\n"
    "The generated algorithm executed successfully on a stochastic objective.\n\n"
    "Final objective error:\n{err_str}\n\n"
    "The result indicates that the current search strategy may not have handled the stochastic evaluations effectively.\n\n"
    "Use the observed result and previous algorithm history to improve the next candidate."
)

WARNINGS_FOOTER_TEMPLATE = (
    "\n\nNumPy/Runtime Warnings raised during execution (these may indicate silent bugs):\n"
    "{warn_str}\n"
    "Check that your code never passes negative values to sqrt, log, or similar functions."
)

PROBLEM_CONTEXT_FOOTER_TEMPLATE = (
    "\n\nProblem context: BBOB-{problem_id}, dim={dim}, bounds=[{lower_bound}, {upper_bound}]."
)

NOISY_PROBLEM_CONTEXT_TEMPLATE = (
    "\n\n[NOISY PROBLEM CONTEXT]\n\n"
    "The objective function is stochastic.\n\n"
    "Ensure that optimization decisions are not based on invalid or inconsistently stored objective values.\n\n"
    "Keep any internal statistical estimates separate from the objective value required by the optimizer interface.\n\n"
    "Ensure that every call to problem(x) is counted against the evaluation budget."
)


class FeedbackRenderer:
    """Renders natural language feedback messages to guide LLM code generation."""

    def render(
        self,
        result: AlgorithmEvaluationResult,
        problem: BaseProblem,
    ) -> str:
        """Render complete feedback message for an algorithm evaluation result.

        Args:
            result: Evaluation outcome from AlgorithmEvaluator domain service.
            problem: Target optimization problem instance.

        Returns:
            str: Actionable diagnostic feedback formatted for the LLM prompt.
        """
        if result.is_failure:
            timed_out = (
                result.metadata.execution.timed_out
                if result.metadata and result.metadata.execution
                else False
            )
            err_type = (
                result.metadata.error.error_type
                if result.metadata and result.metadata.error and result.metadata.error.error_type
                else "ExecutionFailure"
            )
            err_msg = (
                result.metadata.error.error_message
                if result.metadata and result.metadata.error and result.metadata.error.error_message
                else ""
            )
            feedback = self.render_failure(
                error_type=err_type,
                error_message=err_msg,
                problem=problem,
                code_context=result.code_context,
                warnings=result.captured_warnings,
                timed_out=timed_out,
            )
        else:
            feedback = self.render_success(
                final_error=result.final_error,
                problem=problem,
                warnings=result.captured_warnings,
            )

        if result.is_stagnated:
            feedback += META_FEEDBACK_DIVERSITY_INJECTION

        return feedback

    def render_success(
        self,
        final_error: float | None,
        problem: BaseProblem,
        warnings: list[str] | None = None,
    ) -> str:
        """Render natural language feedback for a successful optimization run."""
        err_val = final_error if final_error is not None else 0.0
        if abs(err_val) < 1e-4 and err_val != 0.0:
            err_str = f"{err_val:.6e}"
        else:
            err_str = f"{err_val:.4f}"

        if problem.noise_std > 0:
            msg = SUCCESS_NOISY_FEEDBACK_TEMPLATE.format(err_str=err_str)
        else:
            msg = SUCCESS_CLEAN_FEEDBACK_TEMPLATE.format(err_str=err_str)

        if warnings:
            warn_str = "\n".join(f"  - {w}" for w in warnings)
            msg += WARNINGS_FOOTER_TEMPLATE.format(warn_str=warn_str)

        return msg

    def render_failure(
        self,
        error_type: str,
        error_message: str,
        problem: BaseProblem,
        code_context: str = "",
        warnings: list[str] | None = None,
        timed_out: bool = False,
    ) -> str:
        """Render diagnostic feedback for an execution failure or timeout."""
        if timed_out:
            msg = TIMEOUT_FEEDBACK_TEMPLATE
        else:
            error_str = f"{error_type}: {error_message}" if error_message else f"{error_type}"
            code_section = (
                f"\n\nRelevant code:\n{code_context}" if code_context else ""
            )
            msg = RUNTIME_ERROR_FEEDBACK_TEMPLATE.format(
                error_str=error_str,
                code_section=code_section,
            )

        if warnings:
            warn_str = "\n".join(f"  - {w}" for w in warnings)
            msg += WARNINGS_FOOTER_TEMPLATE.format(warn_str=warn_str)

        lb_val, ub_val = self._extract_bounds(problem)
        problem_id = getattr(problem, "problem_id", "?")
        dim = getattr(problem, "dim", "?")
        msg += PROBLEM_CONTEXT_FOOTER_TEMPLATE.format(
            problem_id=problem_id,
            dim=dim,
            lower_bound=lb_val,
            upper_bound=ub_val,
        )

        if getattr(problem, "noise_std", 0.0) > 0:
            msg += NOISY_PROBLEM_CONTEXT_TEMPLATE

        return msg

    @staticmethod
    def _extract_bounds(problem: BaseProblem) -> tuple[float, float]:
        lb = getattr(problem, "lower_bound", None)
        ub = getattr(problem, "upper_bound", None)
        lb_val = float(lb[0]) if lb is not None and hasattr(lb, "__getitem__") else -5.0
        ub_val = float(ub[0]) if ub is not None and hasattr(ub, "__getitem__") else 5.0
        return lb_val, ub_val
