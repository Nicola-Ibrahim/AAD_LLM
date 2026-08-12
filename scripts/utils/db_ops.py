#!/usr/bin/env python3
"""
db_ops.py
Helper CLI for SQLite database operations (table truncation, row count stats).
"""

import argparse
import os
import sys
from pathlib import Path

def get_engine(db_path: str):
    abs_path = Path(db_path).resolve()
    if not abs_path.exists() and not abs_path.parent.exists():
        abs_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from sqlalchemy import create_engine
        return create_engine(f"sqlite:///{abs_path}")
    except ImportError as e:
        sys.stderr.write(f"Error: SQLAlchemy is required for database operations: {e}\n")
        sys.exit(1)


def cmd_clear_data(args):
    from sqlalchemy import inspect, text
    engine = get_engine(args.db)
    
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = OFF"))
        inspector = inspect(engine)
        tables = [t for t in inspector.get_table_names() if t != "alembic_version"]
        for table in tables:
            conn.execute(text(f"DELETE FROM {table}"))
            print(f"    Cleared table: {table}")
        conn.execute(text("PRAGMA foreign_keys = ON"))
    print("  Done.")


def cmd_table_stats(args):
    from sqlalchemy import inspect, text
    abs_path = Path(args.db).resolve()
    if not abs_path.is_file():
        print(f"  (database file does not exist: {abs_path})")
        return

    engine = get_engine(args.db)
    inspector = inspect(engine)
    tables = [t for t in inspector.get_table_names() if t != "alembic_version"]

    print("  Row Counts:")
    with engine.connect() as conn:
        for table in tables:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"    {table:<25} {count:>6} rows")


def main():
    parser = argparse.ArgumentParser(description="Database Operations Helper CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # clear-data
    p_clear = subparsers.add_parser("clear-data")
    p_clear.add_argument("--db", required=True, help="Path to SQLite database file")

    # table-stats
    p_stats = subparsers.add_parser("table-stats")
    p_stats.add_argument("--db", required=True, help="Path to SQLite database file")

    args = parser.parse_args()

    if args.command == "clear-data":
        cmd_clear_data(args)
    elif args.command == "table-stats":
        cmd_table_stats(args)


if __name__ == "__main__":
    main()
