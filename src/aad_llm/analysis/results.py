import json
from pathlib import Path
from typing import Any


def save_summary(
    history: list[Any],
    problem_id: int,
    dim: int,
    output_dir: str | Path,
    mode: str = "noisy"
) -> Path:
    """
    Collects metadata from the LLaMEA run history and writes a summary.json.
    """
    iterations_data: list[dict[str, Any]] = []
    
    best_iteration = None
    best_error = float('inf')
    best_algo = None

    for i, solution in enumerate(history):
        iteration_num = i + 1
        meta = getattr(solution, 'metadata', {})
        
        # If execution failed completely, meta might be missing, 
        # but we attached it in evaluator's try-except block so it should be there.
        final_error = meta.get("final_error", float('inf'))
        returned_fitness = meta.get("algorithm_returned_fitness", float('inf'))
        algo_name = meta.get("algorithm_name", solution.name)
        
        iteration_entry = {
            "iteration": iteration_num,
            "algorithm": algo_name,
            "algorithm_returned_fitness": returned_fitness,
            "final_error": final_error,
            "timed_out": meta.get("timed_out", False)
        }
        iterations_data.append(iteration_entry)
        
        if final_error < best_error:
            best_error = final_error
            best_iteration = iteration_num
            best_algo = algo_name
            
    # Try to grab true_optimum and noise_std from the first available metadata
    true_optimum = None
    noise_std = None
    if history and hasattr(history[0], 'metadata'):
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
        "iterations": iterations_data
    }

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    summary_file = out_path / "summary.json"
    
    summary_file.write_text(json.dumps(summary_data, indent=4), encoding="utf-8")
        
    return summary_file
