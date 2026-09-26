"""Shared application contract for creating BBOB problem instances."""

from abc import ABC, abstractmethod

from shared.domain.noise_model import NoiseModelEnum
from shared.domain.problem import BaseProblem


class ProblemFactory(ABC):
    """Create configured objective problems through the infrastructure adapter."""

    @abstractmethod
    def create(
        self,
        problem_id: int,
        dim: int,
        noise_std: float,
        noise_model: NoiseModelEnum,
        instance_id: int,
        seed: int,
    ) -> BaseProblem:
        """Create a problem with an explicit condition and random seed."""
