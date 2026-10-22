"""Artifact cleanup must never remove scientific logs or database backups."""

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("command", ["artifacts", "data", "all"])
def test_artifact_cleanup_preserves_ioh_logs_and_results(tmp_path: Path, command: str) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    script = scripts / "clean.sh"
    shutil.copy2(Path(__file__).resolve().parents[1] / "scripts/clean.sh", script)
    preserved = [
        "data/ioh_logs/f15/trace.dat",
        "data/db.sqlite3",
        "results/ioh_traces/f15/trace.dat",
        "results/archives/snapshot/manifest.json",
    ]
    removed = ["data/code/nested/optimizer.py", "data/evolution_state/.checkpoint"]
    for name in preserved + removed:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)

    subprocess.run(
        ["bash", str(script), command],
        input="y\nCLEAN\ny\n",
        text=True,
        capture_output=True,
        check=True,
    )

    for name in preserved:
        assert (tmp_path / name).read_text() == name
    for directory in ("data/code", "data/evolution_state"):
        assert not any((tmp_path / directory).iterdir())
