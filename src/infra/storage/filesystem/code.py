from pathlib import Path
from typing import Any


class CodeRepository:
    """Handles persistence of generated candidate algorithm source code on disk."""

    def __init__(self, base_dir: Path | str):
        self.base_dir = Path(base_dir)

    def save(
        self,
        history: list[Any],
        problem: Any,
        mode: str,
        llm_name: str,
        run_id: int = 1,
    ) -> None:
        """Saves code snippets from iterations to files and updates the metadata with the filepath.

        IMPORTANT: This mutates the history object metadata elements in place.
        """
        code_dir = self.base_dir / "code" / f"bbob{problem.problem_id}" / f"xdim_{problem.dim}" / mode / llm_name / f"run_{run_id}"
        code_dir.mkdir(parents=True, exist_ok=True)

        for i, solution in enumerate(history):
            iteration_num = i + 1
            meta = getattr(solution, "metadata", None)
            if meta and hasattr(solution, "code") and solution.code:
                code_path = code_dir / f"iter_{iteration_num}.py"
                with open(code_path, "w", encoding="utf-8") as f:
                    f.write(solution.code)
                meta.code.code_path = str(code_path)
