from pathlib import Path
from typing import Any


class CheckpointLogger:
    """
    Logger shim that gives LLaMEA a dirname so pickle_archive() fires,
    and optionally flushes accumulated solutions to SQLite every N generations.
    """
    def __init__(
        self,
        dirname: str | Path,
        storage_manager: Any = None,      # ExperimentManager — pass None to skip DB flush
        flush_every: int = 5,             # how many generations between DB flushes
        problem_profile: Any = None,      # ProblemProfile for DB record
        mode: str | None = None,
        llm_name: str | None = None,
        run_id: int = 1,
    ):
        self.dirname = str(dirname)   # ← LLaMEA needs this attr for pickle_archive()
        self.attempt = 0
        self._storage_manager = storage_manager
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
        if self._storage_manager and self._generation % self._flush_every == 0:
            self._flush_to_db()

    def flush_remaining(self):
        """Called manually at the end of a full run to save any leftover generations."""
        if self._storage_manager and self._pending_history:
            self._flush_to_db()

    def _flush_to_db(self):
        if not self._pending_history:
            return
        try:
            self._storage_manager.save_experiment(
                history=list(self._pending_history),
                problem=self._problem_profile,
                mode=self._mode,
                llm_name=self._llm_name,
                run_id=self._run_id,
            )
            self._pending_history = []
        except Exception as e:
            print(f"[!] Periodic DB flush failed (data still in memory): {e}")

    def __getstate__(self):
        state = self.__dict__.copy()
        # Exclude storage manager from pickle since it contains DB connections
        state["_storage_manager"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    # Stubs for LLaMEA methods we don't need
    def log_individual(self, ind): pass
    def log_code(self, attempt, name, code): pass
    def log_conversation(self, role, content): pass
    def log_import_fails(self, fails): pass
    def set_attempt(self, attempt): self.attempt = attempt
