"""Repeating notebook setup must preserve process-worker import identity."""

import ast
import json
import subprocess
import sys
from pathlib import Path


def test_notebook_uses_campaign_without_low_level_llm_access() -> None:
    path = Path(__file__).resolve().parents[1] / "notebooks/02_synthesis.ipynb"
    source = "\n".join(
        "".join(cell["source"])
        for cell in json.loads(path.read_text())["cells"]
        if cell["cell_type"] == "code"
    )
    tree = ast.parse(source)
    assert not any(isinstance(node, ast.Name) and node.id == "LLMClient" for node in ast.walk(tree))
    assert "evolution.infra.llm" not in source
    assert "campaign.model_name" in source


def test_repeated_setup_keeps_synthesis_worker_picklable() -> None:
    project_root = Path(__file__).resolve().parents[1]
    script = """
import json
import pickle
from pathlib import Path

notebook = json.loads(Path('notebooks/02_synthesis.ipynb').read_text())
setup = next(
    ''.join(cell['source']) for cell in notebook['cells']
    if cell['cell_type'] == 'code'
    and 'from evolution.infra.di import EvolutionProvider' in ''.join(cell['source'])
)
namespace = {}
exec(compile(setup, 'notebook-setup', 'exec'), namespace)
from evolution.infra.concurrency.worker import run_synthesis_worker
original_worker = run_synthesis_worker
exec(compile(setup, 'notebook-setup', 'exec'), namespace)
from evolution.infra.concurrency import worker
assert original_worker is worker.run_synthesis_worker
assert pickle.loads(pickle.dumps(original_worker)) is original_worker
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
