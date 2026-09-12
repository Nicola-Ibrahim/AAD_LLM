"""Worker execution harness for evolutionary algorithm synthesis.

Provides the picklable entrypoint executed inside worker processes
to bootstrap storage, instantiate the LLaMEAEngine, and execute the synthesis run.
"""

from pathlib import Path

from shared.config import DATA_DIR
from shared.database.engine import initialize_sqlite_storage
from evolution.application.synthesis_service import EvolutionTask, SessionResult
from evolution.infra.engines.llamea import LLaMEAEngine
from evolution.infra.storage.code.repository import CodeRepository


def run_evolution_worker(task: EvolutionTask) -> SessionResult:
    """Executes an evolution task inside an isolated worker process.

    Args:
        task: EvolutionTask specification containing problem, LLM client, and configuration.

    Returns:
        SessionResult: Outcome of the synthesis session.
    """
    db_path: Path = task.db_path or (DATA_DIR / "db.sqlite3")
    db_repo = initialize_sqlite_storage(db_path)
    code_repo = CodeRepository()
    engine = LLaMEAEngine()

    return engine.run(
        problem=task.problem,
        experiment_id=task.experiment_id,
        prompt_strategy=task.prompt_strategy,
        llm_client=task.llm_client,
        db_repo=db_repo,
        code_repo=code_repo,
        config=task.config,
        initial_iteration=task.initial_iteration,
        synthesis_mode=task.synthesis_mode,
    )
