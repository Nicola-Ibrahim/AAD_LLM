"""Abstract interface and standard telemetry behavior for synthesis logging."""

from abc import ABC, abstractmethod
from collections.abc import Mapping


class BaseLogger(ABC):
    """Base class for synthesis telemetry adapters."""

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose

    @abstractmethod
    def info(self, msg: str) -> None: ...

    @abstractmethod
    def warning(self, msg: str) -> None: ...

    @abstractmethod
    def error(self, msg: str) -> None: ...

    def success(self, msg: str) -> None:
        self.info(f"[SUCCESS] {msg}")

    def header(self, title: str, subtitle: str | None = None, width: int = 80) -> None:
        sub = f" - {subtitle}" if subtitle else ""
        self.info(f"=== {title.upper()}{sub} ===")

    def task_start(
        self,
        index: int,
        total: int,
        model_name: str,
        dim: int,
        noise_std: float,
        problem_id: int,
        strategy: str,
        experiment_id: int,
        problem_name: str = "",
    ) -> None:
        if self.verbose:
            p_name = f" ({problem_name})" if problem_name else ""
            self.info(
                f"[{index}/{total}] Task: {model_name} | {dim}D | noise={noise_std} | "
                f"f{problem_id}{p_name} | {strategy} | Exp ID: #{experiment_id}"
            )

    def generation(
        self,
        gen_idx: int,
        total_gens: int,
        algo_name: str,
        error: float | None,
        fitness: float | None,
        evals_used: int,
        runtime: float,
        is_failure: bool = False,
        failure_reason: str = "",
    ) -> None:
        if self.verbose:
            if not is_failure and error is not None and error < float("inf"):
                fit_str = f", fit={fitness:.4e}" if fitness is not None else ""
                self.info(
                    f"  • Gen {gen_idx}/{total_gens} | Algo: {algo_name} | "
                    f"Error: {error:.4e}{fit_str} | Evals: {evals_used} | Time: {runtime:.2f}s"
                )
            else:
                reason = f" ({failure_reason})" if failure_reason else ""
                self.info(
                    f"  • Gen {gen_idx}/{total_gens} | Algo: {algo_name} | "
                    f"FAILED{reason} | Time: {runtime:.2f}s"
                )

    def resuming(self, exp_id: int, current_iter: int, total_iters: int) -> None:
        self.info(f"Resuming Exp ID: #{exp_id} from Gen {current_iter + 1}/{total_iters}...")

    def cached(self, exp_id: int, total_iters: int, best_error: float | None) -> None:
        err_str = f" (Best Error: {best_error:.4e})" if best_error is not None else ""
        self.info(f"Exp ID: #{exp_id} already completed {total_iters} generations{err_str}. Skipping.")

    def stagnation_warning(self, consecutive_failures: int, threshold: int) -> None:
        self.warning(
            f"Stagnation warning: {consecutive_failures} consecutive failures (threshold: {threshold})"
        )

    def task_complete(
        self,
        exp_id: int,
        best_algo_name: str,
        best_error: float | None,
        raw_obj: float | None = None,
        true_opt: float | None = None,
    ) -> None:
        if best_error is not None and best_error < float("inf"):
            obj_str = f" | Obj: {raw_obj:.6f}" if raw_obj is not None else ""
            self.info(
                f"Exp ID: #{exp_id} complete | Best: {best_algo_name} | "
                f"Final Error: {best_error:.6e}{obj_str}"
            )
        else:
            self.info(f"Exp ID: #{exp_id} incomplete | No valid candidate converged.")

    def audit_summary(
        self,
        model_name: str,
        total_conditions: int,
        completed: int,
        pending: int,
        retry: int,
        progress_pct: float,
    ) -> None:
        self.info(
            f"Synthesis Matrix Audit for '{model_name}': "
            f"{completed}/{total_conditions} completed ({progress_pct:.1f}%), "
            f"{pending} pending, {retry} retry"
        )

    def summary(self, title: str, stats: Mapping[str, object], width: int = 80) -> None:
        self.info(f"--- {title} ---")
        for key, value in stats.items():
            self.info(f"  {key:<26}: {value}")
