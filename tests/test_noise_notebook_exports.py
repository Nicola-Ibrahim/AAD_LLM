"""Notebook 01 exports each landscape view for every configured noise level."""

import json
from pathlib import Path

import plotly.graph_objects as go


def test_landscape_exports_are_partitioned_by_dimension_noise_and_function(
    tmp_path: Path, monkeypatch
) -> None:
    notebook_path = Path(__file__).resolve().parents[1] / "notebooks" / "01_noise.ipynb"
    cells = json.loads(notebook_path.read_text(encoding="utf-8"))["cells"]
    namespace: dict[str, object] = {}
    exported: list[Path] = []

    def record_image(_figure: go.Figure, path: str, **_kwargs: object) -> None:
        exported.append(Path(path))

    monkeypatch.setattr(go.Figure, "write_image", record_image)
    for index in (1, 3):
        exec("".join(cells[index]["source"]), namespace)
    namespace["pub_dir"] = tmp_path
    namespace["TARGET_PROBLEM_IDS"] = (1,)
    namespace["noisy_levels"] = (0.05, 0.1, 0.2)

    for index in (5, 7, 9):
        source = "".join(cells[index]["source"])
        source = source.replace("n_pts = 400", "n_pts = 12")
        source = source.replace("grid_resol = 70", "grid_resol = 8")
        source = source.replace("grid_resol_3d = 50", "grid_resol_3d = 8")
        exec(source, namespace)

    assert len(exported) == 9
    assert {path.parent.relative_to(tmp_path).parts[:2] for path in exported} == {
        ("2D", "std_0.05"),
        ("2D", "std_0.1"),
        ("2D", "std_0.2"),
    }
    assert {path.parent.name for path in exported} == {"f1_sphere"}
    assert {path.name for path in exported} == {
        "figure_1d_noise_cross_section.png",
        "figure_2d_noise_topology.png",
        "figure_3d_noise_surface.png",
    }
