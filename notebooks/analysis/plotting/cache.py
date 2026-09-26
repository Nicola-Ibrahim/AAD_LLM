"""Workflow-specific source signatures and per-figure successful export records."""

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

import plotly.graph_objects as go

from benchmarking.application.analysis import view_data
from benchmarking.application.analysis.view_data import AnalysisInputs
from shared.config import RESULTS_DIR


@dataclass
class FigureCache:
    manifest_path: Path
    signature: str
    force: bool = False
    _entries: dict[str, str] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        try:
            saved = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                self._entries = {str(key): str(value) for key, value in saved.items()}
        except (OSError, ValueError):
            pass

    def needs_export(self, target: Path) -> bool:
        return (
            self.force or not target.is_file() or self._entries.get(str(target)) != self.signature
        )

    def export(self, figure: go.Figure, target: Path) -> None:
        if not self.needs_export(target):
            return
        if target.suffix.lower() != ".png":
            raise ValueError("Analysis figures are PNG-only.")
        target.parent.mkdir(parents=True, exist_ok=True)
        figure.write_image(str(target), scale=3)
        self._entries[str(target)] = self.signature
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.manifest_path.parent,
            prefix=".figure-cache-",
            suffix=".json",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(self._entries, stream, sort_keys=True, indent=2)
        temporary.replace(self.manifest_path)


def build_figure_cache(
    inputs: AnalysisInputs, workflow: str, *, force: bool = False
) -> FigureCache:
    """A transfer update never invalidates native/profile caches."""
    record_groups = {
        "summary": inputs.native_records + inputs.noise_records + inputs.reference_records,
        "profiles": inputs.profile_records,
        "noise": inputs.noise_records,
        "transfer": inputs.transfer_records
        + [r for r in inputs.reference_records if float(r["noise_std"]) == 0.0],
    }
    records = record_groups[workflow]
    digest = hashlib.sha256(b"analysis-workflows-v1")
    settings = inputs.config.model_dump(
        exclude={
            "benchmarking",
            "cross_function_enabled",
            "cross_function_problem_ids",
            "cross_eval_clean_champions",
        }
    )
    if workflow == "transfer":
        settings["cross_function_problem_ids"] = inputs.config.cross_function_problem_ids
    digest.update(json.dumps(settings, sort_keys=True).encode())
    digest.update(json.dumps(inputs.filters, sort_keys=True).encode())
    digest.update(json.dumps(inputs.model_slugs, sort_keys=True).encode())
    digest.update(json.dumps(records, sort_keys=True, default=str).encode())
    for directory in sorted({str(r["trace_directory"]) for r in records if "trace_directory" in r}):
        for path in sorted(Path(directory).rglob("*")):
            if path.is_file() and path.suffix in {".dat", ".json"}:
                digest.update(str(path).encode())
                digest.update(path.read_bytes())
    # Invalidate only plots affected by changed presentation or scientific code.
    plotting = Path(__file__).parent
    names = {
        "summary": ["summary.py"],
        "profiles": ["profiles.py", "performance.py"],
        "noise": ["generalization.py", "profiles.py"],
        "transfer": ["generalization.py"],
    }
    code_files = [plotting / name for name in names[workflow] + ["style.py", "cache.py"]]
    backend = Path(view_data.__file__).resolve().parents[2]
    code_files += list((backend / "domain" / "services").glob("*.py"))
    code_files += list((backend / "application" / "analysis").glob("*.py"))
    for path in sorted(code_files):
        if path.is_file():
            digest.update(path.read_bytes())
    return FigureCache(
        RESULTS_DIR / "reports" / ".analysis_cache" / f"{workflow}.json", digest.hexdigest(), force
    )
