"""Independent, database-synchronized inputs for analysis notebooks."""

from collections import defaultdict
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from benchmarking.application.champions import ChampionCatalog
from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.application.interfaces.candidate_code_reader import CandidateCodeReader
from benchmarking.application.interfaces.evaluation_trace_reader import EvaluationTraceReader
from benchmarking.domain.services.transfer import TransferAnalysisEngine
from benchmarking.domain.vos import EvaluationDataset
from benchmarking.domain.services.resolvers import ModelNames
from benchmarking.domain.services.condition_status import inspect_condition

if TYPE_CHECKING:
    from benchmarking.application.analysis.data import AnalysisData

ChampionIdentity = tuple[str, int, int, str]


@dataclass(frozen=True)
class AnalysisInputs:
    model_names: ModelNames
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


def load_analysis_inputs(
    service: "AnalysisData",
    champions: ChampionCatalog,
    code_reader: CandidateCodeReader,
    transfer_reader: EvaluationTraceReader,
    config: EvaluationConfig,
    *,
    include_transfer: bool = False,
    dims: list[int] | None = None,
    problems: list[int] | None = None,
    noise_stds: list[float] | None = None,
) -> AnalysisInputs:
    """Load each workflow independently, without shared notebook variables."""
    experiments, _ = service.get_synthesis_dataframes()
    completed = experiments.loc[experiments["status"] == "completed"]
    names = service.model_names
    model_labels = {
        str(model): names.get_clean_model_label(str(model))
        for model in completed["llm_name"].dropna().unique()
    }
    model_slugs = {label: names.get_model_slug(raw) for raw, label in model_labels.items()}
    traces = service.load_evaluation_traces(dims=dims, problems=problems, noise_stds=noise_stds)
    solvers = [
        s for s in traces.solvers if " / " not in s or s.split(" / ", 1)[0] in model_labels.values()
    ]
    dataset = traces.filter(solvers=solvers)
    active: set[ChampionIdentity] = set()
    clean_baseline: set[ChampionIdentity] = set()
    for conditions in champions.values():
        for champion in conditions.values():
            path = Path(champion["code_path"])
            if not code_reader.exists(path):
                continue
            code_hash = hashlib.sha256(code_reader.read(path).strip().encode()).hexdigest()
            identity = (champion["llm_name"], champion["problem_id"], champion["dim"], code_hash)
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
        for r in service.trace_repo.load_provenance_records()
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
        for r in TransferAnalysisEngine.frozen_noise_records(records)
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
            for r in transfer_reader.load_provenance_records() + diagonals
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
                (condition.dim, condition.noise_std, condition.problem_id, solver) in valid_traces
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
    return AnalysisInputs(
        model_names=ModelNames(names.registry),
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
