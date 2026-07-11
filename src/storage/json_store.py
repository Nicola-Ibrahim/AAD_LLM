import json
from pathlib import Path

from schema import ExperimentSummary
from storage.base import ExperimentStore


class JsonStore(ExperimentStore):
    """JSON-based storage backend for LLaMEA experiment summaries."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)

    def save(self, summary: ExperimentSummary) -> None:
        """Persists the ExperimentSummary as a summary.json file in structured folders."""
        experiment_name = f"bbob_{summary.problem_id}_dim{summary.dim}_{summary.mode}"
        out_path = self.base_dir / experiment_name / summary.llm_name
        out_path.mkdir(parents=True, exist_ok=True)
        summary_file = out_path / "summary.json"
        summary_file.write_text(json.dumps(summary.to_json_dict(), indent=4), encoding="utf-8")

    def load(
        self,
        problem_id: int | None = None,
        llm_name: str | None = None,
        dim: int | None = None,
        mode: str | None = None,
    ) -> list[ExperimentSummary]:
        """Scans the directory recursively for summary.json files and filters them."""
        summaries: list[ExperimentSummary] = []
        if self.base_dir.exists():
            for summary_file in self.base_dir.glob("**/summary.json"):
                try:
                    data = json.loads(summary_file.read_text(encoding="utf-8"))
                    # Filter in-memory
                    if problem_id is not None and data.get("problem_id") != problem_id:
                        continue
                    if llm_name is not None and data.get("llm_name") != llm_name:
                        continue
                    if dim is not None and data.get("dim") != dim:
                        continue
                    if mode is not None and data.get("mode") != mode:
                        continue
                    summaries.append(ExperimentSummary(**data))
                except Exception:
                    pass
        summaries.sort(key=lambda x: (x.problem_id, x.llm_name))
        return summaries

    def print_table(self) -> None:
        """Prints a formatted table of all found summaries."""
        summaries = self.load()
        if not summaries:
            print(f"No experiment summaries found in '{self.base_dir}'.")
            return

        lines = [
            "=======================================================================================================================",
            "Experiment Results - Collected Summaries from JSON Artifacts",
            "=======================================================================================================================",
            f"{'Problem ID':<10} | {'Dim':<5} | {'Mode':<8} | {'LLM Target':<35} | {'Best Error':<12} | {'Best Algorithm'}",
            "-----------|-------|----------|-------------------------------------|--------------|-----------------------------------",
        ]
        for s in summaries:
            pid = s.problem_id
            dim = s.dim
            mode = s.mode
            llm = s.llm_name
            best_err = s.best_final_error
            best_err_str = (
                f"{best_err:.4f}"
                if isinstance(best_err, (int, float)) and best_err != float("inf")
                else "FAILED"
            )
            best_algo = s.best_algorithm or "N/A"
            lines.append(
                f"{pid:<10} | {dim:<5} | {mode:<8} | {llm:<35} | {best_err_str:<12} | {best_algo}"
            )
        lines.append(
            "======================================================================================================================="
        )
        print("\n".join(lines))
