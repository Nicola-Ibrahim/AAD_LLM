#!/bin/bash
# ============================================================
# db.sh
# Database management and migration CLI for experiments SQLite database.
#
# Usage:
#   bash scripts/db.sh [command] [options]
#
# Commands:
#   upgrade          Apply all pending migrations (default)
#   rollback         Roll back the last migration
#   revision         Autogenerate a new migration script
#   both             Autogenerate + apply a new migration
#   clear            Delete all rows from all tables (keeps schema)
#   reset            Drop and recreate the database from scratch
#   status           Show current migration status and DB stats
#   exit             Exit the CLI
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ─── Load Environment ──────────────────────────────────────
ENV_FILE="$PROJECT_ROOT/.env"
if [ -r "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

# ─── Colors ────────────────────────────────────────────────
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ─── Helpers ───────────────────────────────────────────────
confirm() {
    local prompt="${1:-Are you sure?}"
    local answer
    read -rp "$(echo -e "${YELLOW}${prompt} [y/N]: ${NC}")" answer
    [[ "$answer" =~ ^[Yy]$ ]]
}

confirm_type() {
    # Require the user to type a specific word to confirm a destructive action
    local word="$1"
    local answer
    read -rp "$(echo -e "${RED}  Type '${word}' to confirm: ${NC}")" answer
    [[ "$answer" == "$word" ]]
}

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║       Database Management CLI (AAD-LLM)      ║${NC}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
    echo ""
}

print_db_path() {
    echo -e "  ${BOLD}Database:${NC} $DB_PATH"
    if [[ -f "$DB_PATH" ]]; then
        local size
        size=$(du -sh "$DB_PATH" 2>/dev/null | cut -f1)
        echo -e "  ${BOLD}Size:${NC}     $size"
    else
        echo -e "  ${BOLD}Status:${NC}   ${YELLOW}File does not exist yet${NC}"
    fi
    echo ""
}

# ─── Parse CLI Command ─────────────────────────────────────
COMMAND=""
if [[ $# -gt 0 ]]; then
    case "$1" in
        upgrade|revision|rollback|downgrade|both|revision-upgrade|clear|reset|status)
            COMMAND="$1"
            shift
            ;;
    esac
fi

# ─── Interactive Menu (if no command given) ────────────────
if [[ -z "$COMMAND" ]]; then
    if [[ -t 0 ]]; then
        while true; do
            print_header
            echo -e "  ${BOLD}Select an operation:${NC}"
            echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
            echo -e "    ${BOLD}1)${NC} Apply pending migrations        (upgrade)"
            echo -e "    ${BOLD}2)${NC} Roll back last migration        (rollback)"
            echo -e "    ${BOLD}3)${NC} Create new migration revision   (revision)"
            echo -e "    ${BOLD}4)${NC} Create + apply migration        (both)"
            echo -e "    ${BOLD}5)${NC} Clear all data from tables      (clear)"
            echo -e "    ${BOLD}6)${NC} Reset database from scratch     (reset)"
            echo -e "    ${BOLD}7)${NC} Show migration status & stats   (status)"
            echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
            echo ""
            echo -e "  ${BOLD}Options:${NC}"
            echo -e "    - Type the number of the option to execute (e.g. ${CYAN}'1'${NC})."
            echo -e "    - Press ${YELLOW}Enter${NC} or type ${YELLOW}'q'${NC} to exit."
            echo ""

            read -rp "$(echo -e "  ${BOLD}Your choice:${NC} ")" choice
            choice=$(echo "$choice" | tr '[:upper:]' '[:lower:]' | xargs)

            if [ -z "$choice" ] || [ "$choice" = "q" ] || [ "$choice" = "quit" ] || [ "$choice" = "exit" ]; then
                echo -e "  ${YELLOW}Exiting.${NC}"
                exit 0
            fi

            case "$choice" in
                1) COMMAND="upgrade";  break ;;
                2) COMMAND="rollback"; break ;;
                3)
                    COMMAND="revision"
                    read -rp "  Enter migration message [auto_migration]: " MIGRATE_MSG
                    MIGRATE_MSG="${MIGRATE_MSG:-auto_migration}"
                    set -- -m "$MIGRATE_MSG"
                    break
                    ;;
                4)
                    COMMAND="both"
                    read -rp "  Enter migration message [auto_migration]: " MIGRATE_MSG
                    MIGRATE_MSG="${MIGRATE_MSG:-auto_migration}"
                    set -- -m "$MIGRATE_MSG"
                    break
                    ;;
                5) COMMAND="clear";  break ;;
                6) COMMAND="reset";  break ;;
                7) COMMAND="status"; break ;;
                *)
                    echo -e "  ${RED}✗ ERROR: Invalid choice. Please choose a number between 1 and 7.${NC}"
                    echo ""
                    sleep 1
                    ;;
            esac
        done
    else
        # Non-interactive: default to upgrade
        COMMAND="upgrade"
    fi
fi

# ─── Resolve Database Path ─────────────────────────────────
DB_PATH="${DATABASE_URL:-$PROJECT_ROOT/data/db.sqlite3}"
DB_PATH="${DB_PATH#sqlite:///}"

if [[ ! "$DB_PATH" = /* ]]; then
    DB_PATH="$PROJECT_ROOT/$DB_PATH"
fi

# Ensure the parent directory exists
mkdir -p "$(dirname "$DB_PATH")"

# Export for Alembic env.py
export DATABASE_URL="sqlite:///$DB_PATH"

# ─── Locate Alembic ────────────────────────────────────────
ALEMBIC_CMD="alembic"
if [ -f "$PROJECT_ROOT/.venv/bin/alembic" ]; then
    ALEMBIC_CMD="$PROJECT_ROOT/.venv/bin/alembic"
elif command -v uv &> /dev/null; then
    ALEMBIC_CMD="uv run alembic"
fi

# ─── Locate Python ─────────────────────────────────────────
PYTHON_CMD="python3"
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
elif command -v uv &> /dev/null; then
    PYTHON_CMD="uv run python"
fi

# ─── Print DB info for destructive commands ────────────────
if [[ "$COMMAND" =~ ^(clear|reset|rollback|downgrade)$ ]]; then
    print_header
    print_db_path
fi

# ─── Execute Command ───────────────────────────────────────
case "$COMMAND" in

    upgrade)
        echo -e "  ${GREEN}Applying pending migrations to: $DB_PATH${NC}"
        (cd "$PROJECT_ROOT" && $ALEMBIC_CMD upgrade head)
        echo -e "  ${GREEN}✓ Database is up to date.${NC}"
        ;;

    rollback|downgrade)
        echo -e "  ${YELLOW}Rolling back the last migration on: $DB_PATH${NC}"
        if confirm "This will undo the last schema change. Continue?"; then
            (cd "$PROJECT_ROOT" && $ALEMBIC_CMD downgrade -1)
            echo -e "  ${GREEN}✓ Rollback complete.${NC}"
        else
            echo "  Aborted."
        fi
        ;;

    revision)
        echo -e "  Generating new migration script for: $DB_PATH"
        (cd "$PROJECT_ROOT" && $ALEMBIC_CMD revision --autogenerate "$@")
        echo -e "  ${GREEN}✓ Migration script created.${NC}"
        ;;

    both|revision-upgrade)
        echo -e "  Creating and applying new migration for: $DB_PATH"
        export PREVENT_EMPTY_MIGRATIONS="True"
        if [[ $# -eq 0 ]]; then
            set -- -m "auto_migration"
        fi
        (cd "$PROJECT_ROOT" && $ALEMBIC_CMD revision --autogenerate "$@")
        (cd "$PROJECT_ROOT" && $ALEMBIC_CMD upgrade head)
        echo -e "  ${GREEN}✓ Migration created and applied.${NC}"
        ;;

    clear)
        echo -e "  ${RED}${BOLD}⚠ WARNING: This will DELETE ALL ROWS from every table.${NC}"
        echo -e "  ${BOLD}Database:${NC} $DB_PATH"
        echo ""
        echo -e "  The database schema (tables) will be preserved, but all"
        echo -e "  experiment results, iterations, and stored data will be erased."
        echo ""
        if confirm "Are you sure you want to clear ALL data?"; then
            if confirm_type "CLEAR"; then
                echo -e "\n  ${YELLOW}Clearing all rows...${NC}"
                $PYTHON_CMD - <<EOF
import sys, os
sys.path.insert(0, "$PROJECT_ROOT/src")
os.environ["DATABASE_URL"] = "sqlite:///$DB_PATH"
from sqlalchemy import create_engine, text, inspect

engine = create_engine("sqlite:///$DB_PATH")
with engine.begin() as conn:
    conn.execute(text("PRAGMA foreign_keys = OFF"))
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    # Skip alembic version table
    tables = [t for t in tables if t != "alembic_version"]
    for table in tables:
        conn.execute(text(f"DELETE FROM {table}"))
        print(f"    Cleared table: {table}")
    conn.execute(text("PRAGMA foreign_keys = ON"))
print("  Done.")
EOF
                echo -e "  ${GREEN}✓ All data cleared. Schema intact.${NC}"
            else
                echo -e "  ${YELLOW}Confirmation did not match. Aborted.${NC}"
            fi
        else
            echo "  Aborted."
        fi
        ;;

    reset)
        echo -e "  ${RED}${BOLD}⚠ DANGER: This will DELETE and RECREATE the database file.${NC}"
        echo -e "  ${BOLD}Database:${NC} $DB_PATH"
        echo ""
        echo -e "  ALL data AND schema will be permanently destroyed."
        echo -e "  Migrations will be re-applied from scratch."
        echo ""
        if confirm "Are you absolutely sure you want to RESET the database?"; then
            if confirm_type "RESET"; then
                echo -e "\n  ${YELLOW}Deleting database file...${NC}"
                rm -f "$DB_PATH"
                echo -e "  ${YELLOW}Re-applying all migrations...${NC}"
                (cd "$PROJECT_ROOT" && $ALEMBIC_CMD upgrade head)
                echo -e "  ${GREEN}✓ Database reset complete. Fresh schema applied.${NC}"
            else
                echo -e "  ${YELLOW}Confirmation did not match. Aborted.${NC}"
            fi
        else
            echo "  Aborted."
        fi
        ;;

    status)
        print_header
        print_db_path
        echo -e "  ${BOLD}Migration Status:${NC}"
        (cd "$PROJECT_ROOT" && $ALEMBIC_CMD current) || true
        echo ""
        echo -e "  ${BOLD}Migration History:${NC}"
        (cd "$PROJECT_ROOT" && $ALEMBIC_CMD history --verbose) || true
        if [[ -f "$DB_PATH" ]]; then
            echo ""
            echo -e "  ${BOLD}Row Counts:${NC}"
            $PYTHON_CMD - <<EOF
import sys, os
sys.path.insert(0, "$PROJECT_ROOT/src")
from sqlalchemy import create_engine, text, inspect

engine = create_engine("sqlite:///$DB_PATH")
inspector = inspect(engine)
tables = [t for t in inspector.get_table_names() if t != "alembic_version"]
with engine.connect() as conn:
    for table in tables:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"    {table:<25} {count:>6} rows")
EOF
        fi
        ;;

    *)
        echo -e "  ${RED}Unknown command: '$COMMAND'${NC}"
        echo "  Valid commands: upgrade, rollback, revision, both, clear, reset, status"
        exit 1
        ;;
esac
