import sys
from pathlib import Path
import argparse

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from alembic.config import Config
from alembic import command


def main():
    parser = argparse.ArgumentParser(description="Run SQLite database migrations.")
    parser.add_argument(
        "--db-path",
        default="experiments/results.db",
        help="Path to the SQLite database file (default: experiments/results.db)",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path)
    print(f"Running database migrations for: {db_path.resolve()}")

    try:
        # Load the Alembic configuration
        alembic_cfg = Config("alembic.ini")

        # Override the sqlalchemy.url dynamically to match the target db-path
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.resolve()}")

        # Run upgrade head
        command.upgrade(alembic_cfg, "head")
        print("Database migrations applied successfully!")
    except Exception as e:
        print(f"Error during migration: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
