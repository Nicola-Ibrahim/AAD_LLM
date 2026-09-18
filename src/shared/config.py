import os
from pathlib import Path
from dotenv import load_dotenv

# Root directory of the project (2 levels up from src/shared/config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load environment variables from .env if present
load_dotenv(PROJECT_ROOT / ".env")

# Common directories
CONFIGS_DIR = PROJECT_ROOT / "configs"
CONFIG_DIR = CONFIGS_DIR
DATA_DIR = PROJECT_ROOT / "data"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
SRC_DIR = PROJECT_ROOT / "src"
RESULTS_DIR = PROJECT_ROOT / "results"

# Database connection string
DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'db.sqlite3'}")


