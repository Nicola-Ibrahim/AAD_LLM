from pydantic import BaseModel, Field


class ProblemProfile(BaseModel):
    """Configuration profile of the target optimization problem."""

    problem_id: int = Field(
        description="The BBOB problem ID representing the objective function.", examples=[1, 14, 24]
    )
    dim: int = Field(
        description="Dimension of the search space of the BBOB problem.", examples=[2, 5, 10, 20]
    )
    noise_std: float = Field(
        description="Standard deviation of the Gaussian noise added to the clean evaluations.",
        examples=[0.0, 0.1, 1.0],
    )
    instance_id: int = Field(
        description="The BBOB instance ID chosen for this problem execution run.", examples=[1, 5]
    )
    true_optimum: float | None = Field(
        default=None,
        description="The actual clean theoretical optimum value of the objective function (if known).",
        examples=[79.48],
    )
