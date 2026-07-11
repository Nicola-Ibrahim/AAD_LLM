import json
from pathlib import Path

from schema import ExperimentSummary
from storage.base import ExperimentStore


class JsonStore(ExperimentStore):
    """JSON-based storage backend for LLaMEA experiment summaries."""

    def __init__(self, base_dir: str | Path):
        self._base_dir = Path(base_dir)

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def save(self, summary: ExperimentSummary) -> None:
        """Persists the ExperimentSummary as a summary.json file in structured folders."""
        experiment_name = f"bbob_{summary.problem.problem_id}_dim{summary.problem.dim}_{summary.mode}"
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
                    problem_data = data.get("problem", {})
                    if problem_id is not None and problem_data.get("problem_id") != problem_id:
                        continue
                    if llm_name is not None and data.get("llm_name") != llm_name:
                        continue
                    if dim is not None and problem_data.get("dim") != dim:
                        continue
                    if mode is not None and data.get("mode") != mode:
                        continue
                    summaries.append(ExperimentSummary(**data))
                except Exception:
                    pass
        summaries.sort(key=lambda x: (x.problem.problem_id, x.llm_name))
        return summaries


