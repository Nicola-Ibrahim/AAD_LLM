"""Algorithm Evaluation Result Value Object."""

from pydantic import Field

from evolution.domain.base import ValueObject
from evolution.domain.vos.iteration import IterationMetadata


class AlgorithmEvaluationResult(ValueObject):
    """Immutable domain representation of an algorithm evaluation outcome."""

    fitness_score: float = Field(
        description="Fitness score where higher is better (e.g. -error or failure penalty tier)."
    )
    final_error: float | None = Field(
        default=None,
        description="Absolute error to true optimum |y_clean - y*| if the candidate executed successfully.",
    )
    feedback_message: str | None = Field(
        default=None,
        description="Diagnostic feedback string returned to guide the next synthesis iteration.",
    )
    is_failure: bool = Field(
        description="True if the candidate execution failed, timed out, or produced out-of-bounds return."
    )
    is_stagnated: bool = Field(
        default=False,
        description="True if consecutive failures triggered stagnation meta-feedback.",
    )
    metadata: IterationMetadata = Field(
        description="Complete execution, convergence, code, and error metrics for this evaluation."
    )
    code_context: str = Field(
        default="",
        description="Extracted lines of candidate code around an exception, if available.",
    )
    captured_warnings: list[str] = Field(
        default_factory=list,
        description="NumPy or runtime warnings captured during execution.",
    )
