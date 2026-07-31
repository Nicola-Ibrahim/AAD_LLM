from pathlib import Path

from core.config import DATA_DIR, PROJECT_ROOT


class CodeRepository:
    """Handles persistence of generated candidate algorithm source code on disk."""

    def __init__(self, base_dir: Path = DATA_DIR / "code"):
        self.base_dir = base_dir

    def save_code(
        self,
        code: str,
        iteration_num: int,
        experiment_id: int,
    ) -> Path:
        """Save candidate algorithm source code to disk under its experiment folder.

        Returns the relative Path (from PROJECT_ROOT) to the created iter_N.py file.
        """
        code_dir = self.base_dir / f"experiment_{experiment_id}"
        code_dir.mkdir(parents=True, exist_ok=True)
        code_path = code_dir / f"iter_{iteration_num}.py"
        code_path.write_text(code, encoding="utf-8")

        try:
            return code_path.relative_to(PROJECT_ROOT)
        except ValueError:
            return code_path

    @staticmethod
    def resolve_code_path(code_path: str | Path) -> Path:
        """Resolves a relative or absolute code_path string to an absolute Path on the current system."""
        path = Path(code_path)
        if path.is_absolute():
            return path
        return PROJECT_ROOT / path

    def load_code(self, code_path: str | Path) -> str:
        """Loads and returns the source code string from a stored code_path."""
        full_path = self.resolve_code_path(code_path)
        return full_path.read_text(encoding="utf-8")
