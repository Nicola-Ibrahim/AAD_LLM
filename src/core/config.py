from pathlib import Path

# Root directory of the project (2 levels up from src/core/config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Common directories
DATA_DIR = PROJECT_ROOT / "data"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
SRC_DIR = PROJECT_ROOT / "src"
RESULTS_DIR = PROJECT_ROOT / "results"
