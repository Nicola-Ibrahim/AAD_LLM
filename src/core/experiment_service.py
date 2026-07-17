import threading
from pathlib import Path
from typing import Any
from llamea import LLM
from storage.manager import ExperimentManager
from core.runner import run_evolution_for_problem


def _run_thread(
    noise_std: float,
    llm: LLM,
    problem_cfg: dict[str, Any],
    run_id: int,
    checkpoint_dir: Path,
    storage_manager: ExperimentManager,
    results: dict[str, Any],
    key: str,
    errors: dict[str, Any],
) -> None:
    try:
        from problems.bbob import BBOBProblem
        # Instantiate a thread-local BBOBProblem object
        problem = BBOBProblem(**problem_cfg)

        result = run_evolution_for_problem(
            problem=problem,
            llm=llm,
            noise_std=noise_std,
            run_id=run_id,
            checkpoint_dir=checkpoint_dir,
        )

        # Save to DB via repository facade
        storage_manager.save_experiment(
            history=result.run_history,
            problem=result.problem_profile,
            mode=result.mode,
            llm_name=result.llm_name,
            run_id=run_id,
        )

        # Atomic delete of checkpoint file now that it is safely stored in DB
        problem_id = problem.problem_id
        dim = problem.dim
        ckpt_path = checkpoint_dir / f"run{run_id}_p{problem_id}_d{dim}_{result.mode}.ckpt.json"
        if ckpt_path.exists():
            ckpt_path.unlink()

        results[key] = result
    except Exception as e:
        errors[key] = e


def orchestrate(
    llm: LLM,
    problem_cfg: dict[str, Any],
    run_id: int,
    storage_manager: ExperimentManager,
    checkpoint_dir: Path = Path("data/checkpoints"),
) -> dict[str, Any]:
    """
    Orchestrates Clean and Noisy runs of LLaMEA in parallel threads for resilience and high throughput.

    Parameters
    ----------
    llm : LLM
        Large Language Model interface.
    problem_cfg : dict[str, Any]
        Configuration dictionary passed to BBOBProblem.
    run_id : int
        Unique integer repetition index.
    storage_manager : ExperimentManager
        Persistence coordinator for code blobs and SQLite database records.
    checkpoint_dir : Path, optional
        Directory where localized checkpoints are saved.

    Returns
    -------
    dict[str, Any]
        Dictionary with Clean and Noisy results or raises RuntimeError if execution failed.
    """
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {}
    errors: dict[str, Any] = {}

    thread_clean = threading.Thread(
        target=_run_thread,
        args=(0.0, llm, problem_cfg, run_id, checkpoint_dir, storage_manager, results, "clean", errors),
        name="Thread-Clean",
        daemon=False,
    )
    thread_noisy = threading.Thread(
        target=_run_thread,
        args=(0.5, llm, problem_cfg, run_id, checkpoint_dir, storage_manager, results, "noisy", errors),
        name="Thread-Noisy",
        daemon=False,
    )

    thread_clean.start()
    thread_noisy.start()

    thread_clean.join()
    thread_noisy.join()

    if errors:
        raise RuntimeError(f"Evolution threading run {run_id} failed: {errors}")

    return results
