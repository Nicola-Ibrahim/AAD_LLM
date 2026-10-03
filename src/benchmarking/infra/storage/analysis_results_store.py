"""Versioned numerical analysis snapshots, independent of Plotly and evaluation."""

import hashlib
import io
import json
from dataclasses import asdict
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
import pandas as pd

from benchmarking.application.analysis.results import (
    AnalysisProvenance,
    AttainmentSeries,
    ConditionProfile,
    HardnessSummary,
    NoiseRobustnessResult,
    PerformanceAnalysisResult,
    ProfileAnalysisResult,
    ProfileSeries,
    ReliabilityAnalysisResult,
)

AnalysisResult = (
    ProfileAnalysisResult
    | ReliabilityAnalysisResult
    | NoiseRobustnessResult
    | PerformanceAnalysisResult
)


class AnalysisResultsStore:
    """Save/load calculated results; never load experiments or invoke engines."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def save(self, result: AnalysisResult) -> Path:
        arrays: dict[str, np.ndarray] = {}
        tables: dict[str, pd.DataFrame] = {}
        metadata: dict[str, object] = {
            "schema_version": 1,
            "provenance": asdict(result.provenance),
            "diagnostics": list(result.diagnostics),
        }
        if isinstance(result, ProfileAnalysisResult):
            namespace = Path("profiles") / result.mode
            metadata.update(kind="profiles", mode=result.mode)
            conditions = []
            for index, condition in enumerate(result.conditions):
                prefix = f"condition_{index}"
                arrays[f"{prefix}_evaluations"] = condition.evaluations
                arrays[f"{prefix}_targets"] = condition.targets
                series = []
                for j, curve in enumerate(condition.series):
                    key = f"{prefix}_series_{j}"
                    for name in ("median", "q25", "q75", "ecdf"):
                        arrays[f"{key}_{name}"] = getattr(curve, name)
                    series.append(
                        dict(
                            key=key,
                            solver=curve.solver,
                            problem_id=curve.problem_id,
                            trace_count=curve.trace_count,
                        )
                    )
                conditions.append(
                    dict(
                        key=prefix,
                        model=condition.model,
                        model_slug=condition.model_slug,
                        dim=condition.dim,
                        noise_std=condition.noise_std,
                        problems=condition.problems,
                        solvers=condition.solvers,
                        series=series,
                    )
                )
            metadata["conditions"] = conditions
        elif isinstance(result, ReliabilityAnalysisResult):
            namespace = Path("reliability")
            metadata.update(kind="reliability", model_order=result.model_order)
            tables.update(
                native=result.native, noise_terminal=result.noise_terminal, primary=result.primary
            )
            arrays["evaluations"] = result.evaluations
            series = []
            for index, curve in enumerate(result.attainment):
                key = f"attainment_{index}"
                for name in ("probability", "lower", "upper"):
                    arrays[f"{key}_{name}"] = getattr(curve, name)
                series.append(
                    dict(
                        key=key,
                        solver=curve.solver,
                        baseline=curve.baseline,
                        trace_count=curve.trace_count,
                    )
                )
            metadata["attainment"] = series
        elif isinstance(result, NoiseRobustnessResult):
            namespace = Path("noise_robustness")
            metadata.update(
                kind="noise_robustness",
                model_labels=result.model_labels,
                primary_target=result.primary_target,
            )
            tables.update(conditions=result.conditions, aggregate=result.aggregate)
        elif isinstance(result, PerformanceAnalysisResult):
            namespace = Path("performance")
            metadata.update(
                kind="performance",
                models_to_solvers=result.models_to_solvers,
                model_slugs=result.model_slugs,
                classical_solvers=result.classical_solvers,
                dims=result.dims,
                clean_std=result.clean_std,
                noisy_std=result.noisy_std,
                rankings_name=result.rankings.name,
                rankings_index_name=result.rankings.index.name,
            )
            tables.update(table=result.table, model_scale=result.model_scale)
            tables["rankings"] = result.rankings.rename_axis("solver").reset_index(name="value")
            targets = []
            for index, (noise, values) in enumerate(result.targets.items()):
                key = f"targets_{index}"
                arrays[key] = values
                targets.append(dict(noise_std=noise, key=key))
            metadata["targets"] = targets
            hardness = []
            for index, summary in enumerate(result.hardness):
                entries = []
                for j, (noise, table) in enumerate(summary.tables.items()):
                    key = f"hardness_{index}_{j}"
                    tables[key] = table
                    entries.append(dict(noise_std=noise, key=key))
                hardness.append(
                    dict(
                        model=summary.model,
                        dim=summary.dim,
                        solvers=summary.solvers,
                        tables=entries,
                    )
                )
            metadata["hardness"] = hardness
        else:
            raise TypeError(f"Unsupported analysis result: {type(result).__name__}")

        files: dict[str, bytes] = {}
        buffer = io.BytesIO()
        np.savez_compressed(buffer, **arrays)
        files["arrays.npz"] = buffer.getvalue()
        metadata["tables"] = {
            name: {
                "columns": list(table.columns),
                "dtypes": {str(c): str(t) for c, t in table.dtypes.items()},
                "missing": {
                    str(c): np.flatnonzero(table[c].isna()).tolist() for c in table.columns
                },
                "index": table.index.tolist(),
                "index_name": table.index.name,
                "index_dtype": str(table.index.dtype),
            }
            for name, table in tables.items()
        }
        for name, table in tables.items():
            files[f"{name}.csv"] = table.to_csv(index=False, float_format="%.17g").encode()
        metadata["files"] = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
        encoded = json.dumps(metadata, sort_keys=True, default=str).encode()
        signature = hashlib.sha256(encoded).hexdigest()
        directory = self.root / namespace / signature
        # Commit the manifest last. A partial write is never a loadable snapshot.
        directory.mkdir(parents=True, exist_ok=True)
        for name, data in files.items():
            self._write(directory / name, data)
        self._write(directory / "manifest.json", encoded)
        # Keep established downstream report filenames and CSV schemas.
        reports: dict[str, pd.DataFrame] = {}
        if isinstance(result, ReliabilityAnalysisResult):
            reports = {
                "native_reliability_v1.csv": result.native,
                "noise_robustness_terminal_v1.csv": result.noise_terminal,
            }
        elif isinstance(result, NoiseRobustnessResult):
            reports = {"noise_success_rates_v1.csv": result.aggregate}
        if reports:
            report_dir = self.root.parent / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            for name, table in reports.items():
                self._write(report_dir / name, table.to_csv(index=False).encode())
        return directory

    @staticmethod
    def _write(path: Path, data: bytes) -> None:
        """Replace an individual artifact atomically; clean failed temporary writes."""
        with NamedTemporaryFile(dir=path.parent, prefix=".analysis-", delete=False) as stream:
            temporary = Path(stream.name)
            try:
                stream.write(data)
                stream.flush()
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        try:
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    def load(self, directory: Path) -> AnalysisResult:
        """Restore typed results without pickle, database access or calculations."""
        if not directory.resolve().is_relative_to(self.root.resolve()):
            raise ValueError("Analysis snapshot must be inside the configured results directory.")
        metadata = json.loads((directory / "manifest.json").read_text())
        if metadata["schema_version"] != 1:
            raise ValueError("Unsupported analysis snapshot schema.")
        for name, expected in metadata["files"].items():
            if Path(name).name != name:
                raise ValueError("Invalid snapshot artifact name.")
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
                raise ValueError(f"Analysis snapshot checksum mismatch: {name}")
        with np.load(directory / "arrays.npz", allow_pickle=False) as archive:
            arrays = {name: archive[name].copy() for name in archive.files}
        tables = {}
        for name, spec in metadata["tables"].items():
            if f"{name}.csv" not in metadata["files"]:
                raise ValueError("Unverified snapshot table.")
            if not spec["columns"]:
                tables[name] = pd.DataFrame()
            else:
                tables[name] = pd.read_csv(
                    directory / f"{name}.csv",
                    dtype=spec["dtypes"],
                    float_precision="round_trip",
                    keep_default_na=False,
                    na_values={
                        c: [""]
                        for c, dtype in spec["dtypes"].items()
                        if dtype not in ("object", "str") and not dtype.startswith("string")
                    },
                )
                for column, positions in spec["missing"].items():
                    if positions:
                        tables[name].iloc[positions, tables[name].columns.get_loc(column)] = pd.NA
            tables[name].index = pd.Index(
                spec["index"], dtype=spec["index_dtype"], name=spec["index_name"]
            )
        provenance = AnalysisProvenance(**metadata["provenance"])
        diagnostics = tuple(metadata["diagnostics"])
        kind = metadata["kind"]
        if kind == "profiles":
            conditions = []
            for condition in metadata["conditions"]:
                key = condition["key"]
                curves = [
                    ProfileSeries(
                        c["solver"],
                        c["problem_id"],
                        arrays[f"{c['key']}_median"],
                        arrays[f"{c['key']}_q25"],
                        arrays[f"{c['key']}_q75"],
                        arrays[f"{c['key']}_ecdf"],
                        c["trace_count"],
                    )
                    for c in condition["series"]
                ]
                conditions.append(
                    ConditionProfile(
                        condition["model"],
                        condition["model_slug"],
                        condition["dim"],
                        condition["noise_std"],
                        condition["problems"],
                        condition["solvers"],
                        arrays[f"{key}_evaluations"],
                        arrays[f"{key}_targets"],
                        curves,
                    )
                )
            return ProfileAnalysisResult(metadata["mode"], conditions, provenance, diagnostics)
        if kind == "reliability":
            curves = [
                AttainmentSeries(
                    c["solver"],
                    c["baseline"],
                    arrays[f"{c['key']}_probability"],
                    arrays[f"{c['key']}_lower"],
                    arrays[f"{c['key']}_upper"],
                    c["trace_count"],
                )
                for c in metadata["attainment"]
            ]
            return ReliabilityAnalysisResult(
                tables["native"],
                tables["noise_terminal"],
                tables["primary"],
                arrays["evaluations"],
                curves,
                metadata["model_order"],
                provenance,
                diagnostics,
            )
        if kind == "noise_robustness":
            return NoiseRobustnessResult(
                tables["conditions"],
                tables["aggregate"],
                metadata["model_labels"],
                metadata["primary_target"],
                provenance,
                diagnostics,
            )
        if kind == "performance":
            rankings = tables["rankings"].set_index("solver")["value"]
            rankings.name = metadata["rankings_name"]
            rankings.index.name = metadata["rankings_index_name"]
            hardness = [
                HardnessSummary(
                    s["model"],
                    s["dim"],
                    s["solvers"],
                    {t["noise_std"]: tables[t["key"]] for t in s["tables"]},
                )
                for s in metadata["hardness"]
            ]
            targets = {t["noise_std"]: arrays[t["key"]] for t in metadata["targets"]}
            return PerformanceAnalysisResult(
                targets,
                tables["table"],
                rankings,
                tables["model_scale"],
                hardness,
                metadata["models_to_solvers"],
                metadata["model_slugs"],
                metadata["classical_solvers"],
                metadata["dims"],
                metadata["clean_std"],
                metadata["noisy_std"],
                provenance,
                diagnostics,
            )
        raise ValueError(f"Unsupported analysis snapshot kind: {kind}")
