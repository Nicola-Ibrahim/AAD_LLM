import json
import math
from pathlib import Path
from typing import Any


def sanitize_non_finite_floats(obj: Any) -> Any:
    """
    Recursively replaces float('inf'), float('-inf'), and float('nan') with None (null in JSON).
    """
    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize_non_finite_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_non_finite_floats(v) for v in obj]
    return obj


def save_summary(
    history: list[Any], problem_id: int, dim: int, output_dir: str | Path, mode: str = "noisy"
) -> Path:
    """
    Collects metadata from the LLaMEA run history and writes a summary.json.
    """
    iterations_data: list[dict[str, Any]] = []

    best_iteration = None
    best_error = float("inf")
    best_algo = None

    for i, solution in enumerate(history):
        iteration_num = i + 1
        meta = getattr(solution, "metadata", {})

        # If execution failed completely, meta might be missing,
        # but we attached it in evaluator's try-except block so it should be there.
        final_error = meta.get("final_error", float("inf"))
        raw_fitness = meta.get("raw_fitness", meta.get("algorithm_returned_fitness", float("inf")))
        algo_name = meta.get("algorithm_name", solution.name)

        iteration_entry = {
            "iteration": iteration_num,
            "algorithm": algo_name,
            "raw_fitness": raw_fitness,
            "final_error": final_error,
            "timed_out": meta.get("timed_out", False),
            "runtime_seconds": meta.get("runtime_seconds", 0.0),
            "evaluations_used": meta.get("evaluations_used", 0),
            "budget_consumed_pct": meta.get(
                "budget_consumed_pct", meta.get("budget_utilization_pct", 0.0)
            ),
            "relative_error": meta.get(
                "relative_error", meta.get("normalized_error", float("inf"))
            ),
            "evals_per_second": meta.get("evals_per_second", 0.0),
            "error_per_evaluation": meta.get(
                "error_per_evaluation", meta.get("error_per_eval", float("inf"))
            ),
            "converged": meta.get("converged", False),
            "convergence_threshold": meta.get(
                "convergence_threshold", meta.get("convergence_target", 1e-6)
            ),
            "code_lines": meta.get("code_lines", 0),
            "code_length": meta.get("code_length", meta.get("code_chars", 0)),
            "error_type": meta.get("error_type", None),
            "error_message": meta.get("error_message", None),
            "error_traceback": meta.get("error_traceback", None),
        }
        iterations_data.append(iteration_entry)

        if final_error < best_error:
            best_error = final_error
            best_iteration = iteration_num
            best_algo = algo_name

    # Try to grab true_optimum and noise_std from the first available metadata
    true_optimum = None
    noise_std = None
    if history and hasattr(history[0], "metadata"):
        true_optimum = history[0].metadata.get("true_optimum")
        noise_std = history[0].metadata.get("noise_std")

    summary_data = {
        "problem_id": problem_id,
        "dim": dim,
        "mode": mode,
        "noise_std": noise_std,
        "true_optimum": true_optimum,
        "best_iteration": best_iteration,
        "best_algorithm": best_algo,
        "best_final_error": best_error,
        "iterations": iterations_data,
    }

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    summary_file = out_path / "summary.json"

    clean_summary_data = sanitize_non_finite_floats(summary_data)
    summary_file.write_text(json.dumps(clean_summary_data, indent=4), encoding="utf-8")

    return summary_file


def load_summaries(target_dir: str | Path) -> list[dict[str, Any]]:
    """
    Scans target_dir recursively for summary.json artifact files and loads them into a list.
    """
    path = Path(target_dir)
    summaries: list[dict[str, Any]] = []
    if path.exists():
        for summary_file in path.glob("**/summary.json"):
            try:
                data = json.loads(summary_file.read_text(encoding="utf-8"))
                summaries.append(data)
            except Exception:
                pass
    summaries.sort(key=lambda x: x.get("problem_id", 0))
    return summaries


def print_experiment_summary(target_dir: str | Path) -> None:
    """
    Scans target_dir for saved summary.json artifacts and prints a formatted summary table.
    """
    summaries = load_summaries(target_dir)
    if not summaries:
        print(f"No experiment summaries found in '{target_dir}'.")
        return

    lines = [
        "==========================================================================================",
        "Experiment Results - Collected Summaries from Artifacts",
        "==========================================================================================",
        f"{'Problem ID':<10} | {'Dim':<5} | {'Mode':<8} | {'Best Error':<12} | {'Best Algorithm'}",
        "-----------|-------|----------|--------------|--------------------------------------------",
    ]
    for s in summaries:
        pid = s.get("problem_id", "N/A")
        dim = s.get("dim", "N/A")
        mode = s.get("mode", "N/A")
        best_err = s.get("best_final_error")
        best_err_str = (
            f"{best_err:.4f}"
            if isinstance(best_err, (int, float)) and best_err != float("inf")
            else "FAILED"
        )
        best_algo = s.get("best_algorithm") or "N/A"
        lines.append(f"{pid:<10} | {dim:<5} | {mode:<8} | {best_err_str:<12} | {best_algo}")
    lines.append(
        "=========================================================================================="
    )
    print("\n".join(lines))
