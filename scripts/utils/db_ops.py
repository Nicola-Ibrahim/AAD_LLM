#!/usr/bin/env python3
"""
db_ops.py
Helper CLI for SQLite database operations (table truncation, row count stats).
"""

import argparse
import os
import sqlite3
import sys
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Engine


def cmd_backup(args: argparse.Namespace) -> None:
    """Create and verify a consistent SQLite backup, including committed WAL data."""
    source = Path(args.db).resolve(strict=True)
    if "archives" in source.parts:
        raise ValueError("Archived databases must remain untouched.")
    destination = source.with_name(
        f"{source.name}.{datetime.now(UTC):%Y%m%dT%H%M%S%fZ}.{os.getpid()}.bak"
    )
    destination.touch(exist_ok=False)
    try:
        with closing(sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True)) as reader:
            with closing(sqlite3.connect(destination)) as writer:
                reader.backup(writer)
                if writer.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                    raise RuntimeError("Backup integrity check failed; operation aborted.")
    except Exception:
        destination.unlink()
        raise
    print(f"  Verified backup: {destination}")


def get_engine(db_path: str) -> "Engine":
    abs_path = Path(db_path).resolve()
    if not abs_path.exists() and not abs_path.parent.exists():
        abs_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from sqlalchemy import create_engine

        return create_engine(f"sqlite:///{abs_path}")
    except ImportError as e:
        sys.stderr.write(f"Error: SQLAlchemy is required for database operations: {e}\n")
        sys.exit(1)


def cmd_clear_data(args: argparse.Namespace) -> None:
    from sqlalchemy import inspect, text

    engine = get_engine(args.db)

    try:
        with engine.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys = OFF"))
            inspector = inspect(conn)
            tables = [t for t in inspector.get_table_names() if t != "alembic_version"]
            for table in tables:
                quoted = engine.dialect.identifier_preparer.quote(table)
                conn.execute(text(f"DELETE FROM {quoted}"))
                print(f"    Cleared table: {table}")
            conn.execute(text("PRAGMA foreign_keys = ON"))
    finally:
        engine.dispose()
    print("  Done.")


def cmd_table_stats(args: argparse.Namespace) -> None:
    from sqlalchemy import inspect, text

    abs_path = Path(args.db).resolve()
    if not abs_path.is_file():
        print(f"  (database file does not exist: {abs_path})")
        return

    engine = get_engine(args.db)
    try:
        inspector = inspect(engine)
        tables = [t for t in inspector.get_table_names() if t != "alembic_version"]

        print("  Row Counts:")
        with engine.connect() as conn:
            for table in tables:
                quoted = engine.dialect.identifier_preparer.quote(table)
                count = conn.execute(text(f"SELECT COUNT(*) FROM {quoted}")).scalar()
                print(f"    {table:<25} {count:>6} rows")
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Database Operations Helper CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # clear-data
    p_clear = subparsers.add_parser("clear-data")
    p_clear.add_argument("--db", required=True, help="Path to SQLite database file")

    # table-stats
    p_stats = subparsers.add_parser("table-stats")
    p_stats.add_argument("--db", required=True, help="Path to SQLite database file")

    p_backup = subparsers.add_parser("backup")
    p_backup.add_argument("--db", required=True, help="Path to SQLite database file")

    args = parser.parse_args()

    if args.command == "clear-data":
        cmd_clear_data(args)
    elif args.command == "table-stats":
        cmd_table_stats(args)
    elif args.command == "backup":
        cmd_backup(args)


if __name__ == "__main__":
    main()
