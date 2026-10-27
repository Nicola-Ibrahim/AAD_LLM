from pydantic import Field

from evolution.domain.base import ValueObject
from shared.domain.noise_model import NoiseModelEnum


class ProblemProfile(ValueObject):
    """Configuration profile of the target optimization problem."""

    problem_id: int = Field(
        description="The BBOB problem ID representing the objective function.",
        examples=[1, 14, 24],
        ge=1,
        le=24,
    )
    dim: int = Field(
        description="Dimension of the search space of the BBOB problem.",
        examples=[2, 5, 10, 20],
        gt=0,
    )
    noise_std: float = Field(
        description="Standard deviation factor of the Gaussian noise added to the clean evaluations.",
        examples=[0.0, 0.1, 1.0],
        ge=0,
        allow_inf_nan=False,
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
        gt=0,
    )
    true_optimum: float | None = Field(
        default=None,
        description="The actual clean theoretical optimum value of the objective function (if known).",
        examples=[79.48],
        allow_inf_nan=False,
    )
