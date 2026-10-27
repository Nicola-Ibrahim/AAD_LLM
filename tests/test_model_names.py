"""Recorded model identifiers are preserved; old folders are read through provenance."""

import json

import pytest

from benchmark.application.model_names import baseline_name, folder_solver_name, record_solver_name
from benchmark.infra.io.trace_repository import BenchmarkStateRepository
from shared.application.errors import ArtifactError


@pytest.mark.parametrize(
    "model",
    [
        "qwen2.5-coder-14b-instruct-q4_k_m.gguf",
        "DeepSeek-Coder-V2-Lite-Instruct-Q4_K_M.gguf",
        "gwdg.glm-5.3-flash",
    ],
)
def test_labels_and_new_folders_preserve_the_full_database_name(tmp_path, model):
    folder = f"{model}_baseline"
    record = {"model": model, "strategy": "baseline", "solver_folder": folder}
    assert record_solver_name(record) == f"{model} / baseline"
    assert folder_solver_name(folder) == f"{model} / baseline"
    assert BenchmarkStateRepository(tmp_path).condition_directory(2, 0.0, 1, folder).name == folder


def test_existing_short_folder_is_found_by_recorded_identity(tmp_path):
    state = BenchmarkStateRepository(tmp_path)
    existing = tmp_path / "2D/std_0.0/f1/qwen_14b_baseline"
    existing.mkdir(parents=True)
    record = {"model": "qwen2.5-coder-14b-instruct-q4_k_m.gguf", "strategy": "baseline"}
    (existing / "provenance.json").write_text(json.dumps(record))
    assert state.condition_directory(2, 0.0, 1, record["model"] + "_baseline") == existing
    assert (
        record_solver_name({**record, "solver_folder": existing.name})
        == record["model"] + " / baseline"
    )
    assert existing.exists()


def test_duplicate_recorded_identities_are_reported_instead_of_merging(tmp_path):
    for folder in ("old_a", "old_b"):
        directory = tmp_path / "2D/std_0.0/f1" / folder
        directory.mkdir(parents=True)
        (directory / "provenance.json").write_text(
            json.dumps({"model": "Full.Model", "strategy": "baseline"})
        )
    with pytest.raises(ArtifactError, match="Multiple recorded directories"):
        BenchmarkStateRepository(tmp_path).condition_directory(2, 0.0, 1, "Full.Model_baseline")


def test_baselines_and_modes_have_no_model_alias_inference():
    assert baseline_name("cmaes") == "CMA-ES"
    assert record_solver_name({"baseline": "pso"}) == "PSO"
    assert (
        record_solver_name(
            {
                "model": "Exact.Name.gguf",
                "strategy": "guided",
                "solver_folder": "old_guided_implicit",
            }
        )
        == "Exact.Name.gguf / guided (noise-implicit)"
    )
    assert folder_solver_name("my_pso_research_model") == "my_pso_research_model"


def test_model_names_may_have_provider_namespaces_but_cannot_escape_storage(tmp_path):
    state = BenchmarkStateRepository(tmp_path)
    assert (
        state.condition_directory(2, 0.0, 1, "provider/model_baseline")
        == tmp_path / "2D/std_0.0/f1/provider/model_baseline"
    )
    with pytest.raises(ValueError, match="outside"):
        state.condition_directory(2, 0.0, 1, "../../../../outside_baseline")


def test_existing_folder_lookup_never_substitutes_another_model(tmp_path):
    old = tmp_path / "2D/std_0.0/f1/qwen_14b_baseline"
    old.mkdir(parents=True)
    (old / "provenance.json").write_text(json.dumps({"model": "Qwen-14B", "strategy": "baseline"}))
    assert (
        BenchmarkStateRepository(tmp_path).condition_directory(2, 0.0, 1, "Qwen-32B_baseline")
        == old.parent / "Qwen-32B_baseline"
    )
