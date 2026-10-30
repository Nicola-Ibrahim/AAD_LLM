import shutil
from pathlib import Path

from evolution.domain.interfaces.code_repository import CodeRepository
from shared.application.errors import StorageError
from shared.config import DATA_DIR, PROJECT_ROOT
from shared.infra.artifacts import atomic_write


class FileCodeRepository(CodeRepository):
    """Handles persistence of generated candidate algorithm source code on disk."""

    def __init__(self, base_dir: Path = DATA_DIR / "code") -> None:
        self.base_dir = base_dir

    def save_code(
        self,
        code: str,
        iteration_num: int,
        experiment_id: int,
    ) -> str:
        """Save candidate algorithm source code to disk under its experiment folder.

        Return the relative reference from PROJECT_ROOT, or an absolute reference
        when the configured storage is outside the project.
        """
        code_dir = self.base_dir / f"experiment_{experiment_id}"
        try:
            code_dir.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise StorageError(f"Cannot create code directory: {code_dir}") from error
        code_path = code_dir / f"iter_{iteration_num}.py"
        atomic_write(code_path, code.encode("utf-8"))

        try:
            return str(code_path.relative_to(PROJECT_ROOT))
        except ValueError:
            return str(code_path)

    def clear_experiment(self, experiment_id: int) -> None:
        """Remove the exact per-experiment directory, refusing symbolic links."""
        if experiment_id <= 0:
            raise ValueError("Experiment ID must be positive")
        code_dir = self.base_dir / f"experiment_{experiment_id}"
        if code_dir.is_symlink():
            raise ValueError(f"Refusing to remove symbolic-link code directory: {code_dir}")
        if code_dir.exists():
            try:
                shutil.rmtree(code_dir)
            except OSError as error:
                raise StorageError(f"Cannot clear code directory: {code_dir}") from error
