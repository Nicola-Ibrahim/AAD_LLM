"""Load current, validated scientific inputs through injected read collaborators."""

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from benchmarking.application.analysis.results import AnalysisProvenance
from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.application.interfaces.candidate_code_reader import CandidateCodeReader
from benchmarking.application.interfaces.evaluation_trace_reader import EvaluationTraceReader
from benchmarking.application.interfaces.synthesis_read_repository import SynthesisReadRepository
from benchmarking.application.select_champions import ChampionSelectionService
from benchmarking.domain.services.condition_status import inspect_condition
from benchmarking.domain.services.resolvers import ModelNames
from benchmarking.domain.services.transfer import TransferAnalysisEngine
from benchmarking.domain.vos import EvaluationDataset

ChampionIdentity = tuple[str, int, int, str]


@dataclass(frozen=True)
class AnalysisSnapshot:
    model_labels: dict[str, str]
    solver_labels: dict[str, str]
    config: EvaluationConfig
    dataset: EvaluationDataset
    models_to_solvers: dict[str, list[str]]
    model_slugs: dict[str, str]
    solver_order: list[str]
    classical_solvers: list[str]
    native_records: list[dict[str, object]]
    noise_records: list[dict[str, object]]
    transfer_records: list[dict[str, object]]
    reference_records: list[dict[str, object]]
    profile_records: list[dict[str, object]]
    filters: dict[str, list[int] | list[float] | None]

    @property
    def clean_std(self) -> float:
        return 0.0

    @property
    def noisy_std(self) -> float:
        return next((n for n in self.dataset.noise_stds if n > 0.0), 0.0)

    def provenance(
        self, workflow: Literal["summary", "profiles", "noise", "transfer"]
    ) -> AnalysisProvenance:
        groups = {
            "summary": self.native_records + self.noise_records + self.reference_records,
            "profiles": self.profile_records,
            "noise": self.noise_records,
            "transfer": self.transfer_records
            + [r for r in self.reference_records if float(r["noise_std"]) == 0.0],
        }
        records = groups[workflow]
        settings = self.config.model_dump(
            exclude={
                "benchmarking",
                "cross_function_enabled",
                "cross_function_problem_ids",
                "cross_eval_clean_champions",
            }
        )
        if workflow == "transfer":
            settings["cross_function_problem_ids"] = self.config.cross_function_problem_ids
        digest = hashlib.sha256()
        # Hash detached trace values, not files from presentation code. Terminal-only
        # workflows do not depend on native convergence traces.
        if workflow in {"summary", "profiles"}:
            for condition, solvers in self.dataset.items():
                digest.update(str(condition).encode())
                for solver, runs in solvers.items():
                    digest.update(str(solver).encode())
                    digest.update(str(len(runs)).encode())
                    for run in runs:
                        for values in (run.evaluations, run.raw_objectives):
                            digest.update(str((values.dtype, values.shape)).encode())
                            digest.update(values.tobytes())
        return AnalysisProvenance(
            settings, dict(self.filters), dict(self.model_slugs), records, digest.hexdigest()
        )


class AnalysisDataLoader:
    def __init__(
        self,
        synthesis_repo: SynthesisReadRepository,
        trace_reader: EvaluationTraceReader,
        transfer_reader: EvaluationTraceReader,
        code_reader: CandidateCodeReader,
        champion_selection: ChampionSelectionService,
        model_names: ModelNames,
        config: EvaluationConfig,
        classifier: TransferAnalysisEngine,
    ) -> None:
        self.synthesis_repo = synthesis_repo
        self.trace_reader = trace_reader
        self.transfer_reader = transfer_reader
        self.code_reader = code_reader
        self.champion_selection = champion_selection
        self.model_names = model_names
        self.config = config
        self.classifier = classifier

    def load(
        self,
        *,
        dims: list[int] | None,
        problems: list[int] | None,
        noise_stds: list[float] | None,
        include_transfer: bool = False,
    ) -> AnalysisSnapshot:
        """Preserve current champion, provenance and trace eligibility independently."""
        config = self.config
        champions = self.champion_selection.get_champions()
        experiments, _ = self.synthesis_repo.get_synthesis_dataframes()
        completed = experiments.loc[experiments["status"] == "completed"]
        names = self.model_names
        model_labels = {
            str(model): names.get_clean_model_label(str(model))
            for model in completed["llm_name"].dropna().unique()
        }
        model_slugs = {label: names.get_model_slug(raw) for raw, label in model_labels.items()}
        traces = self.trace_reader.load_evaluation_traces(
            dims=dims,
            problems=problems,
            noise_stds=noise_stds,
            solver_resolver=names.resolve_folder_solver_name,
        )
        solvers = [
            s
            for s in traces.solvers
            if " / " not in s or s.split(" / ", 1)[0] in model_labels.values()
        ]
        dataset = traces.filter(solvers=solvers)
        active: set[ChampionIdentity] = set()
        clean_baseline: set[ChampionIdentity] = set()
        for conditions in champions.values():
            for champion in conditions.values():
                path = Path(champion["code_path"])
                if not self.code_reader.exists(path):
                    continue
                code_hash = hashlib.sha256(self.code_reader.read(path).strip().encode()).hexdigest()
                identity = (
                    champion["llm_name"],
                    champion["problem_id"],
                    champion["dim"],
                    code_hash,
                )
                active.add(identity)
                if (
                    champion.get("mode") == "explicit"
                    and float(champion.get("noise_std", 0.0)) == 0.0
                    and champion.get("prompt_strategy", "baseline") == "baseline"
                ):
                    clean_baseline.add(identity)

        def selected(record: dict[str, object]) -> bool:
            return (
                (not dims or record["dim"] in dims)
                and (not problems or record["problem_id"] in problems)
                and (not noise_stds or record["noise_std"] in noise_stds)
            )

        records = [
            r
            for r in self.trace_reader.load_provenance_records()
            if selected(r)
            and ("baseline" in r or r.get("model") in model_labels)
            and inspect_condition(
                code_available=True,
                directory_exists=True,
                provenance=r,
                expected_code_hash=None,
                expected_trials=config.target_eval_runs,
            ).reason
            in {"complete", "partial", "not_started"}
        ]
        references = [r for r in records if "baseline" in r]
        native = [
            r
            for r in records
            if (r.get("model"), r["problem_id"], r["dim"], r.get("code_hash")) in active
            and (
                r.get("evaluation_kind") == "native"
                or (
                    "evaluation_kind" not in r
                    and (
                        float(r["noise_std"]) == 0.0
                        or str(r.get("solver_folder", "")).endswith(("_implicit", "_noisy"))
                    )
                )
            )
        ]
        noise = [
            r
            for r in self.classifier.frozen_noise_records(records)
            if "baseline" in r
            or (r.get("model"), r["problem_id"], r["dim"], r.get("code_hash")) in active
        ]
        transfer: list[dict[str, object]] = []
        if include_transfer:
            diagonals = [
                r
                for r in native
                if float(r["noise_std"]) == 0.0
                and not str(r.get("solver_folder", "")).endswith("_implicit")
            ]
            transfer = [
                r
                for r in self.transfer_reader.load_provenance_records() + diagonals
                if selected(r)
                and (
                    r.get("model"),
                    r.get("source_problem_id", r["problem_id"]),
                    r["dim"],
                    r.get("code_hash"),
                )
                in clean_baseline
            ]
        profile_records: list[dict[str, object]] = []
        for record in native + noise + references:
            if record not in profile_records:
                profile_records.append(record)
        valid_traces = {
            (
                int(r["dim"]),
                float(r["noise_std"]),
                int(r["problem_id"]),
                names.resolve_folder_solver_name(str(r["solver_folder"])),
            )
            for r in profile_records
        }
        # Current terminal provenance controls identity validity, not the availability
        # or completeness of convergence traces. Never manufacture missing traces.
        dataset = EvaluationDataset(
            conditions_data={
                condition: {
                    solver: runs
                    for solver, runs in by_solver.items()
                    if (condition.dim, condition.noise_std, condition.problem_id, solver)
                    in valid_traces
                }
                for condition, by_solver in dataset.items()
                if any(
                    (condition.dim, condition.noise_std, condition.problem_id, solver)
                    in valid_traces
                    for solver in by_solver
                )
            }
        )
        models: dict[str, list[str]] = defaultdict(list)
        for solver in dataset.solvers:
            if " / " in solver:
                models[solver.split(" / ", 1)[0]].append(solver)
        classical = [s for s in dataset.solvers if " / " not in s]
        llms = [s for s in dataset.solvers if " / " in s]
        return AnalysisSnapshot(
            model_labels={
                str(r.get("model", r.get("baseline", ""))): names.get_clean_model_label(
                    str(r.get("model", r.get("baseline", "")))
                )
                for r in records
            },
            solver_labels={
                str(r["solver_folder"]): str(
                    names.resolve_folder_solver_name(str(r["solver_folder"]))
                )
                for r in records
            },
            config=config,
            dataset=dataset,
            models_to_solvers=dict(models),
            model_slugs=model_slugs,
            solver_order=llms + classical,
            classical_solvers=classical,
            native_records=native,
            noise_records=noise,
            transfer_records=transfer,
            reference_records=references,
            profile_records=profile_records,
            filters={"dims": dims, "problems": problems, "noise_stds": noise_stds},
        )
