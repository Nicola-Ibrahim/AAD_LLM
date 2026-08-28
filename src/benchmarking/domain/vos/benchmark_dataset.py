"""EvaluationDataset Value Object representing complete multi-condition benchmark traces."""

from collections.abc import Iterator, Mapping
from typing import Any, Self
import numpy as np
from pydantic import Field

from benchmarking.domain.base import ValueObject
from benchmarking.domain.vos.condition import EvaluationCondition
from benchmarking.domain.vos.run_trace import RunTrace, SolverRunCollection


class EvaluationDataset(ValueObject, Mapping[EvaluationCondition, dict[str, list[RunTrace]]]):
    """Analytical Value Object encapsulating multi-condition empirical evaluation traces."""

    conditions_data: dict[EvaluationCondition, dict[str, list[RunTrace]]] = Field(
        default_factory=dict,
        description="Map from EvaluationCondition to dictionary of solver names and their run traces.",
    )

    def add_run(
        self,
        condition: EvaluationCondition,
        solver_name: str,
        run: RunTrace,
    ) -> None:
        """Add a single execution run trace to the dataset."""
        if condition not in self.conditions_data:
            self.conditions_data[condition] = {}
        if solver_name not in self.conditions_data[condition]:
            self.conditions_data[condition][solver_name] = []
        self.conditions_data[condition][solver_name].append(run)

    @property
    def dims(self) -> list[int]:
        """List of all unique search space dimensions in the dataset."""
        return sorted(list({c.dim for c in self.conditions_data.keys()}))

    @property
    def noise_stds(self) -> list[float]:
        """List of all unique noise standard deviations in the dataset."""
        return sorted(list({c.noise_std for c in self.conditions_data.keys()}))

    @property
    def problem_ids(self) -> list[int]:
        """List of all unique BBOB problem IDs in the dataset."""
        return sorted(list({c.problem_id for c in self.conditions_data.keys()}))

    @property
    def solvers(self) -> list[str]:
        """List of all unique solver and strategy names in the dataset."""
        all_s: set[str] = set()
        for s_dict in self.conditions_data.values():
            all_s.update(s_dict.keys())
        return sorted(list(all_s))

    def get_runs(
        self,
        dim: int,
        noise_std: float,
        problem_id: int,
        solver: str,
    ) -> list[RunTrace]:
        """Get the list of run traces for a specific condition and solver."""
        cond = EvaluationCondition(dim=dim, noise_std=noise_std, problem_id=problem_id)
        return self.conditions_data.get(cond, {}).get(solver, [])

    def get_solver_collection(
        self,
        dim: int,
        noise_std: float,
        problem_id: int,
        solver: str,
    ) -> SolverRunCollection:
        """Get strongly-typed SolverRunCollection VO for a specific condition and solver."""
        runs = self.get_runs(dim, noise_std, problem_id, solver)
        return SolverRunCollection(solver_name=solver, runs=runs)

    def filter(
        self,
        dims: list[int] | None = None,
        problems: list[int] | None = None,
        noise_stds: list[float] | None = None,
        solvers: list[str] | None = None,
    ) -> Self:
        """Return a filtered sub-dataset."""
        filtered_data: dict[EvaluationCondition, dict[str, list[RunTrace]]] = {}
        for cond, s_dict in self.conditions_data.items():
            if dims and cond.dim not in dims:
                continue
            if problems and cond.problem_id not in problems:
                continue
            if noise_stds and not any(np.isclose(cond.noise_std, n) for n in noise_stds):
                continue

            matching_solvers: dict[str, list[RunTrace]] = {}
            for s_name, runs in s_dict.items():
                if solvers and s_name not in solvers:
                    continue
                matching_solvers[s_name] = runs

            if matching_solvers:
                filtered_data[cond] = matching_solvers

        return self.__class__(conditions_data=filtered_data)

    def __getitem__(self, key: EvaluationCondition) -> dict[str, list[RunTrace]]:
        return self.conditions_data[key]

    def __setitem__(self, key: EvaluationCondition, val: dict[str, list[RunTrace]]) -> None:
        self.conditions_data[key] = val

    def __contains__(self, key: object) -> bool:
        return key in self.conditions_data

    def __iter__(self) -> Iterator[EvaluationCondition]:
        return iter(self.conditions_data)

    def __len__(self) -> int:
        return len(self.conditions_data)

    def items(self):
        return self.conditions_data.items()

    def keys(self):
        return self.conditions_data.keys()

    def values(self):
        return self.conditions_data.values()

    def get(self, key: EvaluationCondition, default: Any = None) -> Any:
        return self.conditions_data.get(key, default)
