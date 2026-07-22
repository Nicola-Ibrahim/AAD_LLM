from pathlib import Path
from typing import Any

from core.config import DATA_DIR


class CodeRepository:
    """Handles persistence of generated candidate algorithm source code on disk."""

    def __init__(self, base_dir: Path = DATA_DIR / "code"):
        self.base_dir = base_dir

    def save_code(
        self,
        code: str,
        iteration_num: int,
        problem: Any,
        mode: str,
        llm_name: str,
        run_id: int,
    ) -> Path:
        """Save candidate algorithm source code to disk under its run folder.

        Returns the absolute Path to the created iter_N.py file.
        """
        code_dir = (
            self.base_dir
            / f"run_{run_id}"
            / f"bbob{problem.problem_id}"
            / f"xdim_{problem.dim}"
            / mode
            / llm_name
        )
        code_dir.mkdir(parents=True, exist_ok=True)
        code_path = code_dir / f"iter_{iteration_num}.py"
        code_path.write_text(code, encoding="utf-8")
        return code_path
