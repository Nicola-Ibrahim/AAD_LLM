import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from core.schema.experiment import ExperimentSummary
from core.schema.iteration import IterationMetadata
from core.schema.problem import ProblemProfile
from infra.storage.base import ExperimentRepository
from infra.storage.run_context import RunContext
from infra.storage.sqlite.tables import ErrorLogORM, ExperimentMode, ExperimentORM, IterationORM


class SQLiteExperimentRepository(ExperimentRepository):
    """SQLite-based repository for LLaMEA experiment summaries and checkpoint management using SQLAlchemy ORM."""

    def __init__(
        self,
        session_factory: sessionmaker,
        checkpoint_dir: Path = Path("data/checkpoints"),
    ):
        self.SessionLocal = session_factory
        self.checkpoint_dir = checkpoint_dir

    def __getstate__(self) -> dict:
        """Strip non-picklable SQLAlchemy session_factory before serialization."""
        state = self.__dict__.copy()
        if "SessionLocal" in state:
            del state["SessionLocal"]
        return state

    def __setstate__(self, state: dict) -> None:
        """Restore state for process workers (SessionLocal will be None)."""
        self.__dict__.update(state)
        if "SessionLocal" not in self.__dict__:
            self.SessionLocal = None

    def create_experiment(
        self,
        problem_id: int,
        dim: int,
        mode: str,
        llm_name: str,
        noise_std: float,
        true_optimum: float,
    ) -> RunContext:
        """Creates the experiment DB row and all pre-execution directories.

        Returns a RunContext with run_id and guaranteed-to-exist directory paths.
        This is the only setup call needed before firing a session.
        """
        with self.SessionLocal() as session:
            mode_enum = ExperimentMode(mode)
            max_id = (
                session.query(func.max(ExperimentORM.run_id))
                .filter_by(
                    problem_id=problem_id,
                    dim=dim,
                    mode=mode_enum,
                    llm_name=llm_name,
                    noise_std=noise_std,
                )
                .scalar()
            )
            run_id = (max_id or 0) + 1
            existing = ExperimentORM(
                problem_id=problem_id,
                dim=dim,
                mode=mode_enum,
                llm_name=llm_name,
                noise_std=noise_std,
                true_optimum=true_optimum,
                run_id=run_id,
                status="running",
                started_at=datetime.now(timezone.utc).isoformat(),
            )
            session.add(existing)
            session.commit()

        experiment_name = f"bbob_{problem_id}_dim{dim}_{mode}"
        archive_dir = self.checkpoint_dir / experiment_name / f"run_{run_id}"
        checkpoint_dir = self.checkpoint_dir / "iterations"
        archive_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        return RunContext(run_id=run_id, archive_dir=archive_dir, checkpoint_dir=checkpoint_dir)

    def _get_checkpoint_paths(
        self, problem_id: int, dim: int, mode: str, run_id: int
    ) -> tuple[Path, Path]:
        """Internal helper to compute archive directory and json checkpoint paths."""
        experiment_name = f"bbob_{problem_id}_dim{dim}_{mode}"
        archive_dir = self.checkpoint_dir / experiment_name / f"run_{run_id}"
        json_path = (
            self.checkpoint_dir
            / "iterations"
            / f"run{run_id}_p{problem_id}_d{dim}_{mode}.ckpt.json"
        )
        return archive_dir, json_path

    def _build_summary_from_envelope(self, envelope: dict) -> ExperimentSummary | None:
        experiment_meta = envelope.get("experiment")
        iterations_data = envelope.get("iterations")

        if not experiment_meta or not iterations_data:
            return None

        problem_meta = ProblemProfile(
            problem_id=experiment_meta["problem_id"],
            dim=experiment_meta["dim"],
            noise_std=experiment_meta["noise_std"],
            instance_id=experiment_meta.get("instance_id", 1),
            true_optimum=experiment_meta.get("true_optimum"),
        )

        iterations = [IterationMetadata(**it) for it in iterations_data]

        best_iteration = None
        best_error = float("inf")
        best_algo = None
        for it in iterations:
            if it.fitness.final_error is not None and it.fitness.final_error < best_error:
                best_error = it.fitness.final_error
                best_iteration = it.iteration
                best_algo = it.algorithm_name

        best_err_val = best_error if best_error != float("inf") else None

        return ExperimentSummary(
            mode=experiment_meta["mode"],
            llm_name=experiment_meta["llm_name"],
            run_id=experiment_meta["run_id"],
            problem=problem_meta,
            best_iteration=best_iteration,
            best_algorithm=best_algo,
            best_final_error=best_err_val,
            iterations=iterations,
        )

    def append_iteration(
        self,
        problem_id: int,
        dim: int,
        mode: str,
        run_id: int,
        metadata: IterationMetadata,
        experiment_meta: dict,
    ) -> None:
        """Atomically appends one IterationMetadata record to the envelope checkpoint JSON."""
        _, json_path = self._get_checkpoint_paths(problem_id, dim, mode, run_id)
        try:
            with json_path.open("r") as f:
                envelope = json.load(f)
        except (json.JSONDecodeError, OSError):
            envelope = {"experiment": experiment_meta, "iterations": []}

        envelope["iterations"].append(metadata.to_json_dict())
        tmp = json_path.with_suffix(".tmp")
        with tmp.open("w") as f:
            json.dump(envelope, f, indent=2)
        tmp.replace(json_path)

    def commit_and_cleanup(self, problem_id: int, dim: int, mode: str, run_id: int) -> None:
        """Parses the local JSON cache, updates SQLite DB, and purges transient checkpoint files."""
        archive_dir, json_path = self._get_checkpoint_paths(problem_id, dim, mode, run_id)
        if not json_path.exists():
            return

        with json_path.open("r") as f:
            envelope = json.load(f)

        summary = self._build_summary_from_envelope(envelope)
        if summary:
            # 1. Save to SQLite database
            self.save(summary)

        # 2. Cleanup files only after processing
        self._delete_checkpoint_files(archive_dir, json_path)

    def commit_without_cleanup(self, problem_id: int, dim: int, mode: str, run_id: int) -> None:
        """Parses local JSON cache and commits to SQLite DB without purging temporary files."""
        _, json_path = self._get_checkpoint_paths(problem_id, dim, mode, run_id)
        if not json_path.exists():
            return

        with json_path.open("r") as f:
            envelope = json.load(f)

        summary = self._build_summary_from_envelope(envelope)
        if summary:
            self.save(summary)

    def _delete_checkpoint_files(self, archive_dir: Path, json_path: Path) -> None:
        if json_path.exists():
            json_path.unlink()
        if archive_dir.exists() and archive_dir.is_dir():
            shutil.rmtree(archive_dir)

    def recover_orphaned(self) -> int:
        """Scans the checkpoint directory for orphaned .ckpt.json files and commits them to DB."""
        recovered_count = 0
        iterations_dir = self.checkpoint_dir / "iterations"
        if not iterations_dir.exists():
            return 0

        for ckpt_path in sorted(iterations_dir.glob("*.ckpt.json")):
            try:
                with ckpt_path.open("r") as f:
                    envelope = json.load(f)

                summary = self._build_summary_from_envelope(envelope)
                if not summary:
                    ckpt_path.unlink()
                    continue

                self.save(summary)
                ckpt_path.unlink()
                recovered_count += 1
                print(
                    f"[recovery] Recovered crashed run {summary.run_id} for "
                    f"BBOB-{summary.problem.problem_id} ({summary.mode})"
                )
            except Exception as e:
                print(f"[recovery] Failed to recover {ckpt_path.name}: {e}")

        return recovered_count

    def save(self, summary: ExperimentSummary) -> None:
        """Updates an ExperimentSummary in the SQLite database using SQLAlchemy."""
        with self.SessionLocal() as session:
            # 1. Look for existing experiment
            existing = (
                session.query(ExperimentORM)
                .filter_by(
                    problem_id=summary.problem.problem_id,
                    dim=summary.problem.dim,
                    mode=ExperimentMode(summary.mode),
                    llm_name=summary.llm_name,
                    noise_std=summary.problem.noise_std,
                    run_id=summary.run_id,
                )
                .first()
            )

            if not existing:
                raise RuntimeError(
                    f"No experiment row found for run_id={summary.run_id}. "
                    "Call create_experiment first."
                )

            # Update experiment summary metrics if summary provides new best metrics
            if summary.best_iteration is not None:
                if existing.best_final_error is None or (
                    summary.best_final_error is not None
                    and summary.best_final_error <= existing.best_final_error
                ):
                    existing.best_final_error = summary.best_final_error
                    existing.best_iteration = summary.best_iteration
                    existing.best_algorithm = summary.best_algorithm

            existing.finished_at = datetime.now(timezone.utc).isoformat()
            existing.status = "completed"

            # Index existing iterations by iteration number to allow in-place upsert
            existing_iters = {it.iteration: it for it in existing.iterations}

            for it in summary.iterations:
                # Flatten the nested Pydantic model into a flat dict mapping to IterationORM columns
                it_dict = it.model_dump()
                flat_dict = {}
                for k, v in it_dict.items():
                    if isinstance(v, dict):
                        # Merge the nested dict fields into the top-level
                        flat_dict.update(v)
                    else:
                        flat_dict[k] = v

                # Add fields from summary.problem into IterationORM
                flat_dict["instance_id"] = summary.problem.instance_id
                flat_dict["noise_std"] = summary.problem.noise_std
                flat_dict["true_optimum"] = summary.problem.true_optimum

                # Filter keys to only columns that exist in IterationORM
                filtered_dict = {
                    k: v for k, v in flat_dict.items() if k in IterationORM.__table__.columns
                }

                error_dict = it_dict.get("error", {})
                error_log = None
                if error_dict.get("error_type"):
                    error_log = ErrorLogORM(
                        error_type=error_dict.get("error_type"),
                        error_message=error_dict.get("error_message"),
                        error_traceback=error_dict.get("error_traceback"),
                    )

                if it.iteration in existing_iters:
                    # Update existing iteration in place
                    curr_it = existing_iters[it.iteration]
                    for k, v in filtered_dict.items():
                        setattr(curr_it, k, v)
                    if error_log:
                        curr_it.error_log = error_log
                else:
                    # Create new iteration
                    iteration = IterationORM(**filtered_dict)
                    if error_log:
                        iteration.error_log = error_log
                    existing.iterations.append(iteration)

            session.commit()

    def load(
        self,
        problem_id: int | None = None,
        llm_name: str | None = None,
        dim: int | None = None,
        mode: str | None = None,
    ) -> list[ExperimentSummary]:
        """Loads and filters ExperimentSummary objects from SQLite database using SQLAlchemy."""
        with self.SessionLocal() as session:
            query = session.query(ExperimentORM)
            if problem_id is not None:
                query = query.filter(ExperimentORM.problem_id == problem_id)
            if llm_name is not None:
                query = query.filter(ExperimentORM.llm_name == llm_name)
            if dim is not None:
                query = query.filter(ExperimentORM.dim == dim)
            if mode is not None:
                query = query.filter(ExperimentORM.mode == ExperimentMode(mode))

            query = query.order_by(ExperimentORM.problem_id.asc(), ExperimentORM.llm_name.asc())
            experiments = query.all()

            summaries: list[ExperimentSummary] = []
            for exp in experiments:
                # Reconstruct the single ProblemProfile for this experiment summary
                instance_id = 1
                if exp.iterations:
                    instance_id = exp.iterations[0].instance_id or 1

                problem_profile = ProblemProfile(
                    problem_id=exp.problem_id,
                    dim=exp.dim,
                    noise_std=exp.noise_std or 0.0,
                    instance_id=instance_id,
                    true_optimum=exp.true_optimum,
                )

                iterations = []
                for it in exp.iterations:
                    # Map SQLAlchemy ORM model to a flat dict
                    row_dict = {
                        col.name: getattr(it, col.name)
                        for col in it.__table__.columns
                        if col.name not in ("id", "experiment_id")
                    }

                    execution_fields = {
                        "timed_out": row_dict.get("timed_out"),
                        "runtime_seconds": row_dict.get("runtime_seconds"),
                        "llm_generation_time": row_dict.get("llm_generation_time"),
                        "evaluations_used": row_dict.get("evaluations_used"),
                        "budget_consumed_pct": row_dict.get("budget_consumed_pct"),
                        "evals_per_second": row_dict.get("evals_per_second"),
                    }
                    fitness_fields = {
                        "raw_fitness": row_dict.get("raw_fitness"),
                        "final_error": row_dict.get("final_error"),
                        "relative_error": row_dict.get("relative_error"),
                        "error_per_evaluation": row_dict.get("error_per_evaluation"),
                    }
                    code_fields = {
                        "code_lines": row_dict.get("code_lines"),
                        "code_length": row_dict.get("code_length"),
                        "code_path": row_dict.get("code_path"),
                    }
                    error_fields = {
                        "error_type": it.error_log.error_type if it.error_log else None,
                        "error_message": it.error_log.error_message if it.error_log else None,
                        "error_traceback": it.error_log.error_traceback if it.error_log else None,
                    }
                    convergence_fields = {
                        "converged": row_dict.get("converged"),
                        "convergence_threshold": row_dict.get("convergence_threshold"),
                    }

                    it_dict = {
                        "algorithm_name": row_dict.get("algorithm_name"),
                        "iteration": row_dict.get("iteration"),
                        "execution": execution_fields,
                        "fitness": fitness_fields,
                        "code": code_fields,
                        "error": error_fields,
                        "convergence": convergence_fields,
                    }

                    iterations.append(IterationMetadata(**it_dict))

                summaries.append(
                    ExperimentSummary(
                        mode=exp.mode.value,
                        llm_name=exp.llm_name,
                        run_id=exp.run_id,
                        problem=problem_profile,
                        best_iteration=exp.best_iteration,
                        best_algorithm=exp.best_algorithm,
                        best_final_error=exp.best_final_error,
                        iterations=iterations,
                    )
                )
        return summaries
