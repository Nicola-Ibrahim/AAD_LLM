"""Frozen-champion noise reliability calculation without exporting."""

from benchmarking.application.analysis.data_loader import AnalysisDataLoader
from benchmarking.application.analysis.results import NoiseRobustnessResult
from benchmarking.domain.services.transfer import TransferAnalysisEngine


class AnalyzeNoiseRobustness:
    def __init__(self, loader: AnalysisDataLoader, engine: TransferAnalysisEngine) -> None:
        self.loader = loader
        self.engine = engine

    def execute(
        self,
        *,
        dims: list[int] | None,
        problems: list[int] | None,
        noise_stds: list[float] | None,
    ) -> NoiseRobustnessResult:
        snapshot = self.loader.load(dims=dims, problems=problems, noise_stds=noise_stds)
        rel = snapshot.config.reliability
        table = self.engine.condition_table(
            self.engine.frozen_noise_records(snapshot.noise_records),
            rel.primary_target,
            rel.secondary_target,
            snapshot.config.target_eval_runs,
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
            table,
            aggregate,
            snapshot.model_labels,
            rel.primary_target,
            snapshot.provenance("noise"),
            diagnostics,
        )
