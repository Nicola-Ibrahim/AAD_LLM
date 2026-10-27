"""Frozen-champion noise reliability calculation without exporting."""

from benchmark.application.analysis.data_loader import AnalysisDataLoader
from benchmark.application.analysis.results import NoiseRobustnessResult
from benchmark.application.interfaces.logger import BenchmarkLoggerInterface
from benchmark.domain.services.transfer import TransferAnalysisEngine


class AnalyzeNoiseRobustness:
    def __init__(
        self,
        loader: AnalysisDataLoader,
        engine: TransferAnalysisEngine,
        logger: BenchmarkLoggerInterface,
    ) -> None:
        self.logger = logger
        self.loader = loader
        self.engine = engine

    def execute(
        self,
        *,
        dims: list[int] | None,
        problems: list[int] | None,
        noise_stds: list[float] | None,
    ) -> NoiseRobustnessResult:
        with self.logger.operation("noise robustness analysis"):
            snapshot = self.loader.load(dims=dims, problems=problems, noise_stds=noise_stds)
            rel = snapshot.config.reliability
            table = self.engine.condition_table(
                self.engine.frozen_noise_records(snapshot.noise_records),
                rel.primary_target,
                rel.secondary_target,
                snapshot.config.trials_per_condition,
            )
            aggregate = self.engine.aggregate_noise(
                table, rel.primary_prompt_strategy, rel.bootstrap_samples, rel.bootstrap_seed
            )
            diagnostics = (
                ()
                if not aggregate.empty and (aggregate["Noise Std"] > 0).any()
                else ("No complete frozen-champion noisy trials.",)
            )
            return NoiseRobustnessResult(
                table, aggregate, rel.primary_target, snapshot.provenance("noise"), diagnostics
            )
