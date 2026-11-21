"""Summarize candidate error and recorded convergence across saved synthesis runs."""

import math
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass

import pandas as pd

from evolution.domain.entities import Experiment
from evolution.domain.enums.experiment_status import ExperimentStatus
from evolution.domain.vos.iteration import IterationMetadata

_RUN_COLUMNS = (
    "experiment_id",
    "model",
    "generations",
    "status",
    "observed_generations",
    "synthesis_seed",
    "problem_id",
    "dim",
    "instance_id",
    "noise_std",
    "noise_model",
    "mode",
    "strategy",
    "budget",
)
_PAIR_COLUMNS = (
    "experiment_id",
    "model",
    "error_at_10",
    "error_at_20",
    "absolute_improvement",
    "relative_improvement",
    "best_after_10",
    "first_convergence_after_10",
)
_SUMMARY_COLUMNS = (
    "model",
    "generations",
    "experiments",
    "valid",
    "converged",
    "median_best_generation",
    "best_after_10",
    "first_convergence_after_10",
)
_PAIRED_SUMMARY_COLUMNS = (
    "model",
    "experiments",
    "valid_prefix",
    "missing_valid_prefix",
    "valid_full_run",
    "comparable",
    "improved",
    "improved_fraction",
    "relative_defined",
    "median_absolute_improvement",
    "median_relative_improvement",
)
_DISTRIBUTION_COLUMNS = (
    "model",
    "generations",
    "generation",
    "best_count",
    "best_fraction",
    "converged_count",
    "cumulative_best_fraction",
    "cumulative_converged_fraction",
)


@dataclass(frozen=True)
class GenerationAnalysis:
    """Per-experiment records and chart-ready summaries. A null model denotes pooling."""

    runs: pd.DataFrame
    exclusions: pd.DataFrame
    summary: pd.DataFrame
    pairs: pd.DataFrame
    paired_summary: pd.DataFrame
    distribution: pd.DataFrame


def _best_candidate(iterations: Sequence[IterationMetadata]) -> tuple[int | None, float | None]:
    best_generation = None
    best_error = None
    for generation, candidate in enumerate(iterations, start=1):
        error = candidate.fitness.final_error
        if (
            error is not None
            and math.isfinite(error)
            and (best_error is None or error < best_error)
        ):
            best_generation = generation
            best_error = error
    return best_generation, best_error


def _model_groups(frame: pd.DataFrame) -> Iterator[tuple[str | None, pd.DataFrame]]:
    yield None, frame
    yield from frame.groupby("model", sort=True)


def _median(series: pd.Series) -> float | None:
    observed = series.dropna()
    return float(observed.median()) if len(observed) else None


def _generation_summary(runs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summaries = []
    distribution = []
    for length, length_runs in runs.groupby("generations", sort=True):
        for model, group in _model_groups(length_runs):
            best = group["best_generation"]
            convergence = group["first_convergence_generation"]
            valid = int(best.count())
            summaries.append(
                (
                    model,
                    length,
                    len(group),
                    valid,
                    int(convergence.count()),
                    _median(best),
                    int(best.gt(10).sum()),
                    int(convergence.gt(10).sum()),
                )
            )
            best_counts = best.value_counts()
            convergence_counts = convergence.value_counts()
            for generation in range(1, int(length) + 1):
                best_count = int(best_counts.get(generation, 0))
                distribution.append(
                    (
                        model,
                        length,
                        generation,
                        best_count,
                        best_count / valid if valid else None,
                        int(convergence_counts.get(generation, 0)),
                        int(best.le(generation).sum()) / valid if valid else None,
                        int(convergence.le(generation).sum()) / len(group),
                    )
                )
    return (
        pd.DataFrame(summaries, columns=_SUMMARY_COLUMNS),
        pd.DataFrame(distribution, columns=_DISTRIBUTION_COLUMNS),
    )


def _paired_summary(pairs: pd.DataFrame) -> pd.DataFrame:
    summaries = []
    for model, group in _model_groups(pairs):
        prefix = int(group["error_at_10"].count())
        absolute = group["absolute_improvement"]
        relative = group["relative_improvement"]
        comparable = int(absolute.count())
        improved = int(absolute.gt(0).sum())
        summaries.append(
            (
                model,
                len(group),
                prefix,
                len(group) - prefix,
                int(group["error_at_20"].count()),
                comparable,
                improved,
                improved / comparable if comparable else None,
                int(relative.count()),
                _median(absolute),
                _median(relative),
            )
        )
    return pd.DataFrame(summaries, columns=_PAIRED_SUMMARY_COLUMNS)


def analyze_generations(experiments: Iterable[Experiment]) -> GenerationAnalysis:
    """Compare recorded generation-10 prefixes to their own full 20-generation runs.

    Only completed experiments with exactly their configured 10 or 20 recorded
    candidates enter the summaries. Failed candidates retain their position.
    A finite final error is required for a best candidate. Equal errors retain the
    earliest generation. Convergence uses the recorded flag for each candidate.
    Relative improvement is a fraction of the best error through generation 10.
    """
    runs = []
    exclusions = []
    pairs = []
    for experiment in experiments:
        length = experiment.max_iterations
        iterations = experiment.iterations
        problem = experiment.problem
        status = experiment.status
        metadata = (
            experiment.id,
            experiment.llm_name,
            length,
            status.value,
            len(iterations),
            experiment.synthesis_seed,
            problem.problem_id,
            problem.dim,
            problem.instance_id,
            problem.noise_std,
            problem.noise_model.value,
            experiment.mode.value,
            experiment.prompt_strategy.value,
            experiment.budget,
        )
        if length not in (10, 20):
            exclusions.append((*metadata, "unsupported_generation_count"))
            continue
        if status != ExperimentStatus.COMPLETED:
            exclusions.append((*metadata, "not_completed"))
            continue
        if len(iterations) != length:
            exclusions.append((*metadata, "iteration_count_mismatch"))
            continue

        best_generation, best_error = _best_candidate(iterations)
        first_convergence = next(
            (
                generation
                for generation, candidate in enumerate(iterations, start=1)
                if candidate.convergence.converged
            ),
            None,
        )
        runs.append((*metadata, best_generation, best_error, first_convergence))

        if length == 20:
            _, prefix_error = _best_candidate(iterations[:10])
            improvement = (
                prefix_error - best_error
                if prefix_error is not None and best_error is not None
                else None
            )
            relative = (
                improvement / prefix_error
                if improvement is not None and prefix_error is not None and prefix_error > 0
                else None
            )
            pairs.append(
                (
                    experiment.id,
                    experiment.llm_name,
                    prefix_error,
                    best_error,
                    improvement,
                    relative,
                    best_generation is not None and best_generation > 10,
                    first_convergence is not None and first_convergence > 10,
                )
            )

    run_frame = pd.DataFrame(
        runs,
        columns=(*_RUN_COLUMNS, "best_generation", "best_error", "first_convergence_generation"),
    )
    pair_frame = pd.DataFrame(pairs, columns=_PAIR_COLUMNS)
    summary, distribution = _generation_summary(run_frame)
    return GenerationAnalysis(
        runs=run_frame,
        exclusions=pd.DataFrame(exclusions, columns=(*_RUN_COLUMNS, "reason")),
        summary=summary,
        pairs=pair_frame,
        paired_summary=_paired_summary(pair_frame),
        distribution=distribution,
    )
