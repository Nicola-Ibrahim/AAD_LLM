from pathlib import Path

from core.config import DATA_DIR


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

        Returns the absolute Path to the created iter_N.py file.
        """
        code_dir = self.base_dir / f"experiment_{experiment_id}"
        code_dir.mkdir(parents=True, exist_ok=True)
        code_path = code_dir / f"iter_{iteration_num}.py"
        code_path.write_text(code, encoding="utf-8")
        return code_path
