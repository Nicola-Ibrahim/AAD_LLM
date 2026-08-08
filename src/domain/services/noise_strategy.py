from abc import ABC, abstractmethod

import numpy as np


from domain.enums import NoiseModelEnum


class BaseNoiseStrategy(ABC):
    """Abstract base class for noise injection strategies into objective values."""

    name: str

    def __init__(self, noise_std: float = 0.0):
        self.noise_std = noise_std

    def setup(
        self,
        clean_problem,
        lb: np.ndarray,
        ub: np.ndarray,
        true_optimum: float,
        seed: int = 42,
    ) -> None:
        """Optional lifecycle hook called during problem initialization for calibration/setup."""
        pass

    @abstractmethod
    def add_noise(self, true_value: float) -> float:
        """Inject noise into the clean true_value."""
        pass


class NoNoiseStrategy(BaseNoiseStrategy):
    """Clean strategy with no noise injection."""

    name: str = NoiseModelEnum.MULTIPLICATIVE.value

    def __init__(self, noise_std: float = 0.0):
        super().__init__(noise_std=0.0)

    def add_noise(self, true_value: float) -> float:
        return true_value


class MultiplicativeNoiseStrategy(BaseNoiseStrategy):
    """Multiplicative Gaussian Noise relative to true optimum gap (Heteroscedastic / CV noise: N(true_val, (noise_std * |true_val - true_optimum|)^2))."""

    name: str = NoiseModelEnum.MULTIPLICATIVE.value

    def __init__(self, noise_std: float = 0.0):
        super().__init__(noise_std=noise_std)
        self.true_optimum: float = 0.0

    def setup(
        self,
        clean_problem,
        lb: np.ndarray,
        ub: np.ndarray,
        true_optimum: float,
        seed: int = 42,
    ) -> None:
        """Store the target global optimum to calculate the optimality gap."""
        self.true_optimum = true_optimum

    def add_noise(self, true_value: float) -> float:
        if self.noise_std <= 0.0:
            return true_value
        dynamic_std = self.noise_std * abs(true_value - self.true_optimum)
        return np.random.normal(true_value, dynamic_std)


class HomoscedasticAdditiveNoiseStrategy(BaseNoiseStrategy):
    """Homoscedastic Additive Gaussian Noise, scaled to problem landscape scale."""

    name: str = NoiseModelEnum.HOMOSCEDASTIC_ADDITIVE.value

    def __init__(self, noise_std: float = 0.0, n_samples: int = 200):
        super().__init__(noise_std=noise_std)
        self.landscape_scale: float = 1.0
        self.n_samples: int = n_samples

    def setup(
        self,
        clean_problem,
        lb: np.ndarray,
        ub: np.ndarray,
        true_optimum: float,
        seed: int = 42,
        n_samples: int | None = None,
    ) -> None:
        """Calibrate landscape scale by sampling clean points across search space bounds."""
        samples_count = n_samples if n_samples is not None else self.n_samples
        np.random.seed(seed)
        sample_points = np.random.uniform(lb, ub, (samples_count, len(lb)))
        sample_y = [clean_problem(x.tolist()) for x in sample_points]
        self.landscape_scale = float(
            np.mean([abs(y - true_optimum) for y in sample_y])
        )
        clean_problem.reset()

    def add_noise(self, true_value: float) -> float:
        if self.noise_std <= 0.0:
            return true_value
        dynamic_std = self.noise_std * self.landscape_scale
        return np.random.normal(true_value, dynamic_std)


class AWGNStrategy(BaseNoiseStrategy):
    """Additive White Gaussian Noise (constant variance: true_val + N(0, noise_std^2))."""

    name: str = NoiseModelEnum.AWGN.value

    def __init__(self, noise_std: float = 0.0):
        super().__init__(noise_std=noise_std)

    def add_noise(self, true_value: float) -> float:
        if self.noise_std <= 0.0:
            return true_value
        return true_value + np.random.normal(0, self.noise_std)


class NoiseStrategyFactory:
    """Factory for instantiating noise strategy objects."""

    _STRATEGIES: dict[str, type[BaseNoiseStrategy]] = {
        NoiseModelEnum.MULTIPLICATIVE.value: MultiplicativeNoiseStrategy,
        NoiseModelEnum.HOMOSCEDASTIC_ADDITIVE.value: HomoscedasticAdditiveNoiseStrategy,
        NoiseModelEnum.AWGN.value: AWGNStrategy,
    }

    @classmethod
    def create(
        cls,
        noise_model: str | NoiseModelEnum | None = None,
        noise_std: float = 0.0,
        **kwargs,
    ) -> BaseNoiseStrategy:
        """Create a BaseNoiseStrategy instance based on noise_model string/enum and noise_std value."""
        if noise_std <= 0.0 or noise_model is None:
            return NoNoiseStrategy()

        model_str = (
            noise_model.value
            if isinstance(noise_model, NoiseModelEnum)
            else str(noise_model).lower()
        )

        strategy_cls = cls._STRATEGIES.get(model_str, MultiplicativeNoiseStrategy)
        return strategy_cls(noise_std=noise_std, **kwargs)




