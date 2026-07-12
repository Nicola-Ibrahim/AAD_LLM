from sqlalchemy.orm import sessionmaker

from schema import ExperimentSummary, IterationMetadata, ProblemProfile
from storage.repository import ExperimentRepository
from storage.sqlite.models import ExperimentORM, IterationORM


class SQLiteExperimentRepository(ExperimentRepository):
    """SQLite-based repository for LLaMEA experiment summaries using SQLAlchemy ORM."""

    def __init__(self, session_factory: sessionmaker):
        self.SessionLocal = session_factory

    def save(self, summary: ExperimentSummary) -> None:
        """Saves or updates an ExperimentSummary in the SQLite database using SQLAlchemy."""
        with self.SessionLocal() as session:
            # 1. Look for existing experiment
            existing = (
                session.query(ExperimentORM)
                .filter_by(
                    problem_id=summary.problem.problem_id,
                    dim=summary.problem.dim,
                    mode=summary.mode,
                    llm_name=summary.llm_name,
                )
                .first()
            )

            if existing:
                session.delete(existing)
                session.flush()  # Cascade deletes iterations immediately

            # 2. Map Pydantic model to ORM models
            experiment = ExperimentORM(
                problem_id=summary.problem.problem_id,
                dim=summary.problem.dim,
                mode=summary.mode,
                llm_name=summary.llm_name,
                noise_std=summary.problem.noise_std,
                true_optimum=summary.problem.true_optimum,
                best_iteration=summary.best_iteration,
                best_algorithm=summary.best_algorithm,
                best_final_error=summary.best_final_error,
            )

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

                # Add fields from summary.problem into IterationORM, since the columns still exist
                flat_dict["instance_id"] = summary.problem.instance_id
                flat_dict["noise_std"] = summary.problem.noise_std
                flat_dict["true_optimum"] = summary.problem.true_optimum

                # filter keys to only columns that exist in IterationORM
                filtered_dict = {
                    k: v for k, v in flat_dict.items() if k in IterationORM.__table__.columns
                }
                iteration = IterationORM(**filtered_dict)
                experiment.iterations.append(iteration)

            session.add(experiment)
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
                query = query.filter(ExperimentORM.mode == mode)

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
                        "error_type": row_dict.get("error_type"),
                        "error_message": row_dict.get("error_message"),
                        "error_traceback": row_dict.get("error_traceback"),
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
                        mode=exp.mode,
                        llm_name=exp.llm_name,
                        problem=problem_profile,
                        best_iteration=exp.best_iteration,
                        best_algorithm=exp.best_algorithm,
                        best_final_error=exp.best_final_error,
                        iterations=iterations,
                    )
                )
        return summaries
