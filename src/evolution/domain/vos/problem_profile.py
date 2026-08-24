from pydantic import Field

from evolution.domain.base import ValueObject
from evolution.domain.enums import NoiseModelEnum


class ProblemProfile(ValueObject):
    """Configuration profile of the target optimization problem."""

    problem_id: int = Field(
        description="The BBOB problem ID representing the objective function.", examples=[1, 14, 24]
    )
    dim: int = Field(
        description="Dimension of the search space of the BBOB problem.", examples=[2, 5, 10, 20]
    )
    noise_std: float = Field(
        description="Standard deviation factor of the Gaussian noise added to the clean evaluations.",
        examples=[0.0, 0.1, 1.0],
    )
    noise_model: NoiseModelEnum = Field(
        default=NoiseModelEnum.HETEROSCEDASTIC,
        description="Noise strategy applied for noisy evaluation.",
        examples=[
            NoiseModelEnum.HETEROSCEDASTIC,
            NoiseModelEnum.HOMOSCEDASTIC_ADDITIVE,
            NoiseModelEnum.AWGN,
            NoiseModelEnum.NONE,
        ],
    )
    instance_id: int = Field(
        default=1,
        description="The BBOB instance ID chosen for this problem execution run.",
        examples=[1, 5],
    )
    true_optimum: float | None = Field(
        default=None,
        description="The actual clean theoretical optimum value of the objective function (if known).",
        examples=[79.48],
    )
