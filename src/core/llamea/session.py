from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Tuple

from llamea import LLaMEA
from infra.llm.client import LLMClient
from core.llamea.prompts import (
    TASK_PROMPT_CLEAN,
    TASK_PROMPT_NOISY,
    EXAMPLE_PROMPT,
    FORMAT_PROMPT,
)
from core.llamea.evaluator import Evaluator
from infra.storage.sqlite.mapper import build_experiment_summary

from core.problems.bbob import BBOBProblem
from infra.storage.base import ExperimentRepository
from infra.storage.filesystem.code import CodeRepository
from infra.storage.checkpoint.repository import CheckpointRepository, CheckpointState


class CheckpointLogger:
    """
    Logger shim that gives LLaMEA a dirname so pickle_archive() fires,
    and optionally flushes accumulated solutions to SQLite every N generations.
    """
    def __init__(
        self,
        dirname: str | Path,
        db_repo: ExperimentRepository,
        code_repo: CodeRepository,
        flush_every: int = 5,
        problem_profile: Any = None,
        mode: str | None = None,
        llm_name: str | None = None,
        run_id: int = 1,
    ):
        self.dirname = str(dirname)
        self.attempt = 0
        self._db_repo = db_repo
        self._code_repo = code_repo
        self._flush_every = flush_every
        self._problem_profile = problem_profile
        self._mode = mode
        self._llm_name = llm_name
        self._run_id = run_id
        self._pending_history: list = []
        self._generation = 0

    def log_population(self, population):
        """Called by LLaMEA after every generation."""
        self._generation += 1
        self._pending_history.extend(population)
        if self._generation % self._flush_every == 0:
            self._flush_to_db()

    def flush_remaining(self):
        """Called manually at the end of a full run to save any leftover generations."""
        if self._pending_history:
            self._flush_to_db()

    def _flush_to_db(self):
        if not self._pending_history:
            return
        try:
            # 1. Save code (mutates pending history elements in place)
            self._code_repo.save(
                history=self._pending_history,
                problem=self._problem_profile,
                mode=self._mode,
                llm_name=self._llm_name,
            )

            # 2. Build summary
            summary = build_experiment_summary(
                history=list(self._pending_history),
                problem=self._problem_profile,
                mode=self._mode,
                llm_name=self._llm_name,
            )
            summary.run_id = self._run_id

            # 3. Save to DB
            self._db_repo.save(summary)
            self._pending_history = []
        except Exception as e:
            print(f"[!] Periodic DB flush failed (data still in memory): {e}")

    def __getstate__(self):
        state = self.__dict__.copy()
        # Exclude repositories from pickle since they contain DB connections
        state["_db_repo"] = None
        state["_code_repo"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    # Stubs for LLaMEA methods we don't need
    def log_individual(self, ind): pass
    def log_code(self, attempt, name, code): pass
    def log_conversation(self, role, content): pass
    def log_import_fails(self, fails): pass
    def set_attempt(self, attempt): self.attempt = attempt


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
        llm: LLMClient,
        checkpoint_repo: CheckpointRepository,
        db_repo: ExperimentRepository,
        code_repo: CodeRepository,
        budget: int = 1000,
        iterations: int = 10,
        noise_std: float = 0.0,
        run_id: int = 1,
        flush_every: int = 5,
        cleanup_on_completion: bool = True,
    ):
        """Initializes the synthesis session with its parameters and required repositories.

        Args:
            problem: The BBOB problem optimization target.
            llm: The LLM controller interface to optimize the solution.
            checkpoint_repo: Repository handling checkpoints for recovery.
            db_repo: Repository persisting experiment summary metrics.
            code_repo: Repository saving synthesized algorithm files.
            budget: Code evaluation budget.
            iterations: Count of evolutionary loop iterations.
            noise_std: Standard deviation of evaluation noise.
            run_id: Unique run execution number.
            flush_every: Intermediate DB sync frequency (in generations).
            cleanup_on_completion: Delete checkpoint archives on clean run exits.
        """
        self._problem = problem
        self._llm_client = llm
        self._checkpoint_repo = checkpoint_repo
        self._db_repo = db_repo
        self._code_repo = code_repo
        self._budget = budget
        self._iterations = iterations
        self._noise_std = noise_std
        
        # Resolve llm_name explicitly from the LLM provider
        if isinstance(llm, LLMClient):
            self._llm_name = llm.llm_name
        else:
            raw_name = getattr(llm, "model", "unknown")
            self._llm_name = Path(raw_name).name.replace(":", "_").replace("/", "_").replace("\\", "_")

        self._run_id = run_id
        self._flush_every = flush_every
        self._cleanup_on_completion = cleanup_on_completion

        # Derived fields
        self._problem_id = problem.problem_id
        self._dim = problem.dim
        self._mode = "noisy" if noise_std > 0.0 else "clean"
        self._experiment_name = f"bbob_{self._problem_id}_dim{self._dim}_{self._mode}"

    def run(self) -> SessionResult:
        """Runs the complete evolution loop for the problem."""
        print(f"\n--- Starting LLaMEA Evolution for BBOB-{self._problem_id} (Dim {self._dim}, Mode {self._mode}) ---")

        task_prompt = self._resolve_task_prompt()
        ckpt_state = self._resolve_checkpoint()
        evaluator = self._setup_evaluator(ckpt_state)
        
        optimizer, is_resumed = self._create_optimizer(evaluator, ckpt_state, task_prompt)
        self._attach_logger(optimizer, ckpt_state, is_resumed, evaluator)

        # Run loop
        archive_path = str(ckpt_state.archive_dir) if is_resumed else None
        optimizer.run(archive_path=archive_path)

        if optimizer.logger:
            optimizer.logger.flush_remaining()

        # Final persistence and cleanup
        self._save_final_results(optimizer, evaluator)
        self._cleanup_checkpoint(ckpt_state)

        # Report and return result
        self._print_report(optimizer.best_so_far)

        return self._build_session_result(optimizer.best_so_far, optimizer, evaluator)

    def _resolve_checkpoint(self) -> CheckpointState:
        """Resolves the checkpoint state for the current problem run from the repository."""
        return self._checkpoint_repo.resolve(
            problem_id=self._problem_id,
            dim=self._dim,
            mode=self._mode,
            run_id=self._run_id,
        )


    def _create_optimizer(
        self, evaluator: Evaluator, ckpt_state: CheckpointState, task_prompt: str
    ) -> Tuple[LLaMEA, bool]:
        """Creates a new LLaMEA optimizer or resumes from a warm-start pickle checkpoint if it exists."""
        resume = ckpt_state.pickle_exists
        is_resumed = False
        optimizer = None

        if resume:
            print(f"[i] Checkpoint found — resuming from {ckpt_state.archive_dir}")
            try:
                optimizer = LLaMEA.warm_start(str(ckpt_state.archive_dir))
                if optimizer is not None:
                    optimizer.f = evaluator
                    optimizer.llm = self._llm_client.native_llm
                    is_resumed = True
                    print(f"[i] Resumed at generation {optimizer.generation}, "
                          f"history size {len(optimizer.run_history)}")
            except Exception as e:
                print(f"[!] Warm start failed, starting fresh: {e}")
                optimizer = None

        if optimizer is None:
            optimizer = LLaMEA(
                f=evaluator,
                llm=self._llm_client.native_llm,
                n_parents=1,
                n_offspring=1,
                budget=self._iterations,
                task_prompt=task_prompt,
                example_prompt=EXAMPLE_PROMPT,
                output_format_prompt=FORMAT_PROMPT,
                experiment_name=self._experiment_name,
                elitism=True,
                log=False,
                max_workers=1,
                parallel_backend="sequential",
            )

        return optimizer, is_resumed

    def _resolve_task_prompt(self) -> str:
        """Constructs the structured task prompt based on the problem characteristics and noise profile."""
        return (TASK_PROMPT_NOISY if self._mode == "noisy" else TASK_PROMPT_CLEAN).format(
            problem_id=self._problem_id,
            dim=self._dim,
            lower_bound=self._problem.lower_bound,
            upper_bound=self._problem.upper_bound,
        )

    def _setup_evaluator(self, ckpt_state: CheckpointState) -> Evaluator:
        """Initializes the problem evaluator, binding problem data, budget limits, and checkpointer path."""
        return Evaluator(
            problem=self._problem,
            budget=self._budget,
            noise_std=self._noise_std,
            run_id=self._run_id,
            json_checkpoint_path=ckpt_state.json_path,
            experiment_meta={
                "run_id": self._run_id,
                "problem_id": self._problem_id,
                "dim": self._dim,
                "mode": self._mode,
                "noise_std": self._noise_std,
                "llm_name": self._llm_name,
            },
        )

    def _attach_logger(
        self, optimizer: LLaMEA, ckpt_state: CheckpointState, is_resumed: bool, evaluator: Evaluator
    ) -> None:
        """Configures and binds a CheckpointLogger shim to the optimizer for database sync and checkpointing."""
        if is_resumed and optimizer.logger is not None:
            # Rehydrate the deserialized logger with live DB connections
            optimizer.logger._db_repo = self._db_repo
            optimizer.logger._code_repo = self._code_repo
            optimizer.log = True
        else:
            ckpt_logger = CheckpointLogger(
                dirname=ckpt_state.archive_dir,
                db_repo=self._db_repo,
                code_repo=self._code_repo,
                flush_every=self._flush_every,
                problem_profile=evaluator.problem_profile,
                mode=self._mode,
                llm_name=self._llm_name,
                run_id=self._run_id,
            )
            optimizer.logger = ckpt_logger
            optimizer.log = True

    def _save_final_results(self, optimizer: LLaMEA, evaluator: Evaluator) -> None:
        """Persists the candidate code files and the overall experiment summaries to the database."""
        self._code_repo.save(
            history=optimizer.run_history,
            problem=evaluator.problem_profile,
            mode=self._mode,
            llm_name=self._llm_name,
            run_id=self._run_id,
        )

        summary = build_experiment_summary(
            history=optimizer.run_history,
            problem=evaluator.problem_profile,
            mode=self._mode,
            llm_name=self._llm_name,
        )
        summary.run_id = self._run_id
        self._db_repo.save(summary)

    def _cleanup_checkpoint(self, ckpt_state: CheckpointState) -> None:
        """Deletes transient checkpoint archives upon successful completion of the evolutionary run."""
        if self._cleanup_on_completion:
            self._checkpoint_repo.delete(ckpt_state)

    def _build_session_result(self, best_sol: Any, optimizer: LLaMEA, evaluator: Evaluator) -> SessionResult:
        """Constructs and returns the immutable SessionResult contract summarizing the optimization run."""
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
            problem_id=self._problem_id,
            dim=self._dim,
            mode=self._mode,
            noise_std=self._noise_std,
            best_error=best_error if best_error != float("inf") else None,
            run_id=self._run_id,
            run_history=optimizer.run_history,
            experiment_name=self._experiment_name,
            llm_name=self._llm_name,
            best_solution=best_sol,
            error_msg=None,
            problem_profile=evaluator.problem_profile,
        )

    def _print_report(self, best_sol: Any) -> None:
        """Prints a human-readable console report highlighting objective value and error metrics of the best candidate."""
        if best_sol is not None:
            meta = getattr(best_sol, "metadata", None)
            try:
                returned_val = meta.fitness.raw_fitness
                true_opt = self._problem.true_optimum
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
            print(f"=== BBOB-{self._problem_id} Evolution Best Solution Summary ({self._mode.upper()}) ===")
            print(f"  Best Algorithm Name:       {best_sol.name}")
            print(f"  Returned Objective Value:  {val_str}")
            print(f"  True Global Optimum:       {opt_str}")
            print(f"  Final Absolute Error:       {err_str} (Target = 0.0)")
            print(f"  Negated Error (LLaMEA Fitness): {fit_str} [= -|error|, higher is better]")
            print("=" * 65 + "\n")
