"""Select champion candidates using application-owned ranking policy."""

from pathlib import Path
import pandas as pd

from benchmarking.application.ports import Champion, ChampionCatalog, ChampionRepository


class ChampionSelectionService:
    """Select best candidates per model, function, dimension, strategy, and mode."""

    def __init__(
        self,
        champions_repo: ChampionRepository,
    ) -> None:
        self.champions_repo = champions_repo

    @staticmethod
    def select_candidates(rows: pd.DataFrame) -> ChampionCatalog:
        champions: ChampionCatalog = {}
        if rows.empty:
            return champions

        grouped = rows.groupby(["llm_name", "problem_id", "dim", "prompt_strategy"])
        for (model, problem_id, dim, strategy), group in grouped:
            model_name = str(model)
            model_champions = champions.setdefault(model_name, {})

            def add_best(subset: pd.DataFrame, mode: str, noise_std: float) -> None:
                if subset.empty:
                    return
                best = subset.iloc[0]
                key = f"f{problem_id}_{dim}D_{mode}_std{noise_std}_{strategy}"
                model_champions[key] = {
                    "problem_id": int(problem_id),
                    "dim": int(dim),
                    "mode": mode.removesuffix("_explicit"),
                    "noise_std": float(noise_std),
                    "prompt_strategy": str(strategy),
                    "experiment_id": int(best["experiment_id"]),
                    "iteration_id": int(best["iteration_id"]),
                    "algorithm_name": str(best["algorithm_name"]),
                    "final_error": float(best["final_error"]),
                    "evaluations_used": (
                        int(best["evaluations_used"])
                        if pd.notnull(best["evaluations_used"])
                        else None
                    ),
                    "code_path": str(best["code_path"]),
                    "llm_name": model_name,
                }

            explicit = group[group["mode"] == "explicit"]
            clean = explicit[explicit["noise_std"] == 0.0]
            add_best(clean, "explicit", 0.0)
            noisy = explicit[explicit["noise_std"] > 0.0]
            for noise_std, subset in noisy.groupby("noise_std"):
                add_best(subset, "explicit", float(noise_std))
            implicit = group[group["mode"] == "implicit"]
            for noise_std, subset in implicit.groupby("noise_std"):
                add_best(subset, "implicit", float(noise_std))
        return champions

    def get_champions(self) -> ChampionCatalog:
        return self.select_candidates(self.champions_repo.query_candidates())

    def flatten_champions(
        self, champions_dict: ChampionCatalog | None = None
    ) -> dict[str, Champion]:
        champions = champions_dict if champions_dict is not None else self.get_champions()
        flat: dict[str, Champion] = {}
        for model, conditions in champions.items():
            if isinstance(conditions, dict) and "code_path" in conditions:
                flat[model] = conditions
            elif isinstance(conditions, dict):
                flat.update({f"{model}/{key}": value for key, value in conditions.items()})
        return flat

    def export_champions(
        self, output_path: Path | None = None
    ) -> tuple[ChampionCatalog, pd.DataFrame]:
        champions = self.get_champions()
        self.champions_repo.write_champions_json(champions, output_path)
        summary_rows = [
            {"model": model, "key": key, **candidate}
            for model, conditions in champions.items()
            for key, candidate in conditions.items()
        ]
        return champions, pd.DataFrame(summary_rows)


__all__ = ["ChampionSelectionService"]
