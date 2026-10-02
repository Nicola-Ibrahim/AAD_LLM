"""Read-only post-evaluation summary of current champions and classical baselines."""

from pathlib import Path

import pandas as pd

from benchmarking.application.evaluation.workload import EvaluationWorkload
from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.application.interfaces.evaluation_state_store import EvaluationStateStore
from benchmarking.application.select_champions import ChampionSelectionService
from benchmarking.domain.services.evaluation_outcomes import summarize_trial_outcomes


def summarize_evaluations(
    workload: EvaluationWorkload,
    selection: ChampionSelectionService,
    state: EvaluationStateStore,
    config: EvaluationConfig,
) -> pd.DataFrame:
    """Use current workload validity; stale and incomplete trials never suggest synthesis."""
    conditions = pd.concat(
        [workload.audit_champions_workload(), workload.audit_baselines_workload()],
        ignore_index=True,
    )
    champions = selection.flatten_champions()
    rows = []
    for _, condition in conditions.iterrows():
        if condition.get("is_filtered", False):
            continue
        baseline = condition["solver_type"] == "baseline"
        champion = {} if baseline else champions.get(condition.get("raw_key", condition["key"]), {})
        directory = (
            state.eval_dir
            / f"{condition['dim']}D"
            / f"std_{condition['noise_std']}"
            / f"f{condition['problem_id']}"
            / condition["solver"]
            if baseline
            else Path(condition["target_dir"])
        )
        provenance = state.read_provenance(directory) or {}
        outcome = summarize_trial_outcomes(
            provenance,
            config.target_eval_runs,
            config.reliability.primary_target,
            config.reliability.secondary_target,
        )
        category = outcome.category
        reusable = condition["reason"] in {"complete", "partial", "not_started"}
        if not reusable:
            category = "missing_or_stale"
        if category == "missing_or_stale":
            action = "Refresh benchmark/code first"
        elif category == "incomplete":
            action = "Finish/resume benchmark first"
        elif category in {"all_failed", "mostly_failed"}:
            action = (
                "Inspect baseline implementation"
                if baseline
                else "Inspect; consider fresh synthesis"
            )
        elif category == "some_failed":
            action = "Inspect failed-trial diagnostics"
        elif category == "large_error":
            action = "Compare with baselines; not an automatic rerun"
        else:
            action = "No execution-failure flag"
        rows.append(
            {
                "Model": condition["model"],
                "Experiment ID": champion.get("experiment_id"),
                "Algorithm": champion.get("algorithm_name", condition["solver"]),
                "Mode": str(condition.get("mode", "")),
                "Strategy": condition["strategy"],
                "Problem ID": int(condition["problem_id"]),
                "Dim": int(condition["dim"]),
                "Noise": float(condition["noise_std"]),
                "Solver Type": condition["solver_type"],
                "Recorded trials": outcome.recorded_trials,
                "Executed trials": outcome.executed_trials,
                "Valid trials": outcome.executed_trials - outcome.failed_trials if reusable else 0,
                "Expected trials": config.target_eval_runs,
                "Failed trials": outcome.failed_trials if reusable else 0,
                "Execution rate": (
                    (outcome.executed_trials - outcome.failed_trials) / outcome.executed_trials
                    if reusable and outcome.executed_trials
                    else float("nan")
                ),
                "Failure rate": (
                    outcome.failed_trials / outcome.executed_trials
                    if reusable and outcome.executed_trials
                    else float("nan")
                ),
                "Solved trials": outcome.solved_trials if reusable else 0,
                "Meaningful trials": outcome.meaningful_trials if reusable else 0,
                "Primary target rate": outcome.success_rate if reusable else float("nan"),
                "Median error": outcome.median_error if reusable else float("nan"),
                "Median finite error": outcome.median_finite_error if reusable else float("nan"),
                "Category": category,
                "Suggested action": action,
                "Rerun candidate": not baseline
                and category in {"all_failed", "mostly_failed"}
                and bool(champion.get("experiment_id")),
            }
        )
    table = pd.DataFrame(rows)
    if table.empty:
        return table
    keys = ["Problem ID", "Dim", "Noise"]
    baseline_errors = (
        table[
            (table["Solver Type"] == "baseline")
            & (table["Executed trials"] >= config.target_eval_runs)
            & (table["Category"] != "missing_or_stale")
        ]
        .groupby(keys)["Median error"]
        .min()
        .rename("Best baseline median error")
    )
    table = table.join(baseline_errors, on=keys)
    table["Experiment ID"] = pd.array(table["Experiment ID"], dtype="Int64")
    return table.sort_values(
        ["Model", "Problem ID", "Dim", "Noise", "Strategy", "Mode"], kind="stable"
    ).reset_index(drop=True)
