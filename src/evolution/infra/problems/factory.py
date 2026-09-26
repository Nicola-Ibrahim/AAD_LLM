"""IOH-backed factory for concrete BBOB problem adapters."""

from evolution.domain.enums import NoiseModelEnum
from shared.application.interfaces.problem_factory import ProblemFactory
from evolution.domain.services.noise_strategy import NoiseStrategyFactory
from evolution.infra.problems.bbob import BBOBProblem


class BBOBProblemFactory(ProblemFactory):
    def create(
        self,
        problem_id: int,
        dim: int,
        noise_std: float,
        noise_model: NoiseModelEnum,
        instance_id: int = 1,
        seed: int = 42,
    ) -> BBOBProblem:
        noise_strategy = NoiseStrategyFactory.create(noise_model, noise_std)
        return BBOBProblem(
            problem_id=problem_id,
            dim=dim,
            noise_strategy=noise_strategy,
            instance_id=instance_id,
            seed=seed,
        )
