"""Repeating notebook setup must preserve process-worker import identity."""

import subprocess
import sys
from pathlib import Path


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
    and 'from bootstrap.synthesis import build_synthesis_campaign' in ''.join(cell['source'])
)
namespace = {}
exec(compile(setup, 'notebook-setup', 'exec'), namespace)
from bootstrap.synthesis import run_synthesis_worker
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
