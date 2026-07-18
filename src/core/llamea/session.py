import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Tuple

from llamea import LLaMEA, LLM
from core.problems.bbob import BBOBProblem
from core.llamea.prompts import (
    TASK_PROMPT_CLEAN,
    TASK_PROMPT_NOISY,
    EXAMPLE_PROMPT,
    FORMAT_PROMPT,
)
from core.llamea.evaluator import Evaluator
from core.checkpoint.logger import CheckpointLogger
from infra.storage.checkpoint.repository import CheckpointRepository, CheckpointState


@dataclass
class SessionResult:
    """Immutable contract returned per-problem by LLaMEASession.run()."""
    problem_id: int
    dim: int
    mode: str
    noise_std: float
    best_error: float | None
    run_id: int = 1
    run_history: list[Any] = field(default_factory=list)
    experiment_name: str = ""
    llm_name: str = ""
    error_msg: str | None = None
    best_solution: Any = None
    problem_profile: Any = None


class LLaMEASession:
    """Manages the lifecycle of a single LLaMEA synthesis session on a BBOB problem."""

    def __init__(
        self,
        problem: BBOBProblem,
        llm: LLM,
        budget: int = 1000,
        iterations: int = 10,
        noise_std: float = 0.0,
        llm_name: str = "unknown",
        run_id: int = 1,
        checkpoint_repo: CheckpointRepository | None = None,
        storage_manager: Any = None,
        flush_every: int = 5,
    ):
        self.problem = problem
        self.llm = llm
        self.budget = budget
        self.iterations = iterations
        self.noise_std = noise_std
        self.llm_name = llm_name
        self.run_id = run_id
        self.checkpoint_repo = checkpoint_repo
        self.storage_manager = storage_manager
        self.flush_every = flush_every

        # Derived fields
        self.problem_id = problem.problem_id
        self.dim = problem.dim
        self.mode = "noisy" if noise_std > 0.0 else "clean"
        self.experiment_name = f"bbob_{self.problem_id}_dim{self.dim}_{self.mode}"

    def run(self) -> SessionResult:
        """Runs the complete evolution loop for the problem."""
        # 1. Resolve prompt
        task_prompt = (TASK_PROMPT_NOISY if self.mode == "noisy" else TASK_PROMPT_CLEAN).format(
            problem_id=self.problem_id,
            dim=self.dim,
            lower_bound=self.problem.lower_bound,
            upper_bound=self.problem.upper_bound,
        )

        print(f"\n--- Starting LLaMEA Evolution for BBOB-{self.problem_id} (Dim {self.dim}, Mode {self.mode}) ---")

        # 2. Setup Evaluator
        ckpt_state = self._resolve_checkpoint()
        evaluator = Evaluator(
            problem=self.problem,
            budget=self.budget,
            noise_std=self.noise_std,
            run_id=self.run_id,
            json_checkpoint_path=ckpt_state.json_path if ckpt_state else None,
            experiment_meta={
                "run_id": self.run_id,
                "problem_id": self.problem_id,
                "dim": self.dim,
                "mode": self.mode,
                "noise_std": self.noise_std,
                "llm_name": self.llm_name,
            },
        )

        # 3. Create/resume optimizer
        optimizer, is_resumed = self._create_optimizer(evaluator, ckpt_state, task_prompt)

        # 4. Attach CheckpointLogger
        if ckpt_state is not None:
            ckpt_logger = CheckpointLogger(
                dirname=ckpt_state.archive_dir,
                storage_manager=self.storage_manager,
                flush_every=self.flush_every,
                problem_profile=evaluator.problem_profile,
                mode=self.mode,
                llm_name=self.llm_name,
                run_id=self.run_id,
            )
            optimizer.logger = ckpt_logger
            optimizer.log = True
            if is_resumed:
                ckpt_logger._pending_history = list(optimizer.run_history)
                ckpt_logger._generation = optimizer.generation

        # 5. Run loop
        optimizer.run(archive_path=str(ckpt_state.archive_dir) if (ckpt_state and is_resumed) else None)

        if ckpt_state and optimizer.logger:
            optimizer.logger.flush_remaining()

        # 6. Report and return result
        best_sol = optimizer.best_so_far
        self._print_report(best_sol)

        best_error = float("inf")
        if best_sol is not None:
            meta = getattr(best_sol, "metadata", None)
            try:
                final_err = meta.fitness.final_error
            except AttributeError:
                meta = getattr(best_sol, "metadata", {})
                final_err = meta.get("final_error", getattr(best_sol, "fitness", "N/A"))

            if isinstance(final_err, (int, float)):
                best_error = final_err

        return SessionResult(
            problem_id=self.problem_id,
            dim=self.dim,
            mode=self.mode,
            noise_std=self.noise_std,
            best_error=best_error if best_error != float("inf") else None,
            run_id=self.run_id,
            run_history=optimizer.run_history,
            experiment_name=self.experiment_name,
            llm_name=self.llm_name,
            best_solution=best_sol,
            error_msg=None,
            problem_profile=evaluator.problem_profile,
        )

    def _resolve_checkpoint(self) -> CheckpointState | None:
        if not self.checkpoint_repo:
            return None
        return self.checkpoint_repo.resolve(
            problem_id=self.problem_id,
            dim=self.dim,
            mode=self.mode,
            run_id=self.run_id,
        )

    def _create_optimizer(
        self, evaluator: Evaluator, ckpt_state: CheckpointState | None, task_prompt: str
    ) -> Tuple[LLaMEA, bool]:
        resume = ckpt_state.pickle_exists if ckpt_state else False
        is_resumed = False
        optimizer = None

        if resume and ckpt_state:
            print(f"[i] Checkpoint found — resuming from {ckpt_state.archive_dir}")
            try:
                optimizer = LLaMEA.warm_start(str(ckpt_state.archive_dir))
                if optimizer is not None:
                    optimizer.f = evaluator
                    optimizer.llm = self.llm
                    is_resumed = True
                    print(f"[i] Resumed at generation {optimizer.generation}, "
                          f"history size {len(optimizer.run_history)}")
            except Exception as e:
                print(f"[!] Warm start failed, starting fresh: {e}")
                optimizer = None

        if optimizer is None:
            optimizer = LLaMEA(
                f=evaluator,
                llm=self.llm,
                n_parents=1,
                n_offspring=1,
                budget=self.iterations,
                task_prompt=task_prompt,
                example_prompt=EXAMPLE_PROMPT,
                output_format_prompt=FORMAT_PROMPT,
                experiment_name=self.experiment_name,
                elitism=True,
                log=False,
                max_workers=1,
                parallel_backend="sequential",
            )

        return optimizer, is_resumed

    def _print_report(self, best_sol: Any) -> None:
        if best_sol is not None:
            meta = getattr(best_sol, "metadata", None)
            try:
                returned_val = meta.fitness.raw_fitness
                true_opt = self.problem.true_optimum
                final_err = meta.fitness.final_error
            except AttributeError:
                meta = getattr(best_sol, "metadata", {})
                returned_val = meta.get("raw_fitness", "N/A")
                true_opt = meta.get("true_optimum", "N/A")
                final_err = meta.get("final_error", getattr(best_sol, "fitness", "N/A"))

            err_str = f"{final_err:.6e}" if isinstance(final_err, (int, float)) else str(final_err)
            val_str = f"{returned_val:.6f}" if isinstance(returned_val, (int, float)) else str(returned_val)
            opt_str = f"{true_opt:.6f}" if isinstance(true_opt, (int, float)) else str(true_opt)
            fit_str = (
                f"{best_sol.fitness:.6e}"
                if hasattr(best_sol, "fitness") and isinstance(best_sol.fitness, (int, float))
                else "N/A"
            )

            print("\n" + "=" * 65)
            print(f"=== BBOB-{self.problem_id} Evolution Best Solution Summary ({self.mode.upper()}) ===")
            print(f"  Best Algorithm Name:       {best_sol.name}")
            print(f"  Returned Objective Value:  {val_str}")
            print(f"  True Global Optimum:       {opt_str}")
            print(f"  Final Absolute Error:       {err_str} (Target = 0.0)")
            print(f"  Negated Error (LLaMEA Fitness): {fit_str} [= -|error|, higher is better]")
            print("=" * 65 + "\n")
