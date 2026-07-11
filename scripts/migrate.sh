#!/bin/bash
# ============================================================
# migrate.sh
# Central CLI wrapper for database migrations using Alembic.
#
# Usage:
#   bash scripts/migrate.sh [upgrade|revision|rollback] [options]
#
# Examples:
#   bash scripts/migrate.sh           -> Auto-detect schema changes & upgrade database
#   bash scripts/migrate.sh revision  -> Autogenerate a new migration script
#   bash scripts/migrate.sh rollback  -> Roll back last migration
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Parse Command (default: upgrade)
COMMAND=""
if [[ $# -gt 0 ]]; then
    if [[ "$1" == "upgrade" || "$1" == "revision" || "$1" == "rollback" || "$1" == "downgrade" || "$1" == "both" || "$1" == "revision-upgrade" ]]; then
        COMMAND="$1"
        shift
    fi
fi

# If no command is provided, prompt the user if in an interactive terminal
if [[ -z "$COMMAND" ]]; then
    if [[ -t 0 ]]; then
        echo "========================================================"
        echo "  Alembic Database Migration CLI"
        echo "========================================================"
        echo "No command specified. Please select an option:"
        options=(
            "Run database migrations (upgrade)"
            "Create new migration revision (revision)"
            "Create and apply a new migration revision (both)"
            "Roll back last database migration (rollback)"
            "Exit"
        )
        COLUMNS=1
        select opt in "${options[@]}"; do
            if [[ -z "$opt" && -z "$REPLY" ]]; then
                echo "No selection made. Exiting."
                exit 0
            fi
            case $REPLY in
                1)
                    COMMAND="upgrade"
                    break
                    ;;
                2)
                    COMMAND="revision"
                    read -rp "Enter migration message [auto_migration]: " MIGRATE_MSG
                    MIGRATE_MSG="${MIGRATE_MSG:-auto_migration}"
                    set -- -m "$MIGRATE_MSG"
                    break
                    ;;
                3)
                    COMMAND="both"
                    read -rp "Enter migration message [auto_migration]: " MIGRATE_MSG
                    MIGRATE_MSG="${MIGRATE_MSG:-auto_migration}"
                    set -- -m "$MIGRATE_MSG"
                    break
                    ;;
                4)
                    COMMAND="rollback"
                    break
                    ;;
                5)
                    echo "Exiting."
                    exit 0
                    ;;
                *)
                    echo "Invalid option. Please choose a number between 1 and 5."
                    ;;
            esac
        done
    else
        COMMAND="upgrade"
    fi
fi

# Define database path (default: experiments/results.db relative to root)
DB_PATH="${DATABASE_URL:-$PROJECT_ROOT/experiments/results.db}"
# Strip sqlite:/// prefix if present to get raw path
DB_PATH="${DB_PATH#sqlite:///}"

# Resolve database to absolute path
if [[ ! "$DB_PATH" = /* ]]; then
    DB_PATH="$PROJECT_ROOT/$DB_PATH"
fi

# Ensure the database parent directory exists
mkdir -p "$(dirname "$DB_PATH")"

# Locate the Alembic CLI runner
ALEMBIC_CMD="alembic"
if [ -f "$PROJECT_ROOT/.venv/bin/alembic" ]; then
    ALEMBIC_CMD="$PROJECT_ROOT/.venv/bin/alembic"
    elif command -v uv &> /dev/null; then
    ALEMBIC_CMD="uv run alembic"
fi

# Export DATABASE_URL so env.py reads it
export DATABASE_URL="sqlite:///$DB_PATH"

if [[ "$COMMAND" == "rollback" || "$COMMAND" == "downgrade" ]]; then
    echo "Rolling back last database migration on: $DB_PATH"
    (cd "$PROJECT_ROOT" && $ALEMBIC_CMD downgrade -1)
elif [[ "$COMMAND" == "revision" ]]; then
    echo "Creating new migration revision for: $DB_PATH"
    (cd "$PROJECT_ROOT" && $ALEMBIC_CMD revision --autogenerate "$@")
elif [[ "$COMMAND" == "both" || "$COMMAND" == "revision-upgrade" ]]; then
    echo "Creating and applying a new migration revision for: $DB_PATH"
    export PREVENT_EMPTY_MIGRATIONS="True"
    if [[ $# -eq 0 ]]; then
        set -- -m "auto_migration"
    fi
    (cd "$PROJECT_ROOT" && $ALEMBIC_CMD revision --autogenerate "$@")
    echo "Applying migrations..."
    (cd "$PROJECT_ROOT" && $ALEMBIC_CMD upgrade head)
    echo "Database migrations applied successfully!"
else
    echo "Running database migrations for: $DB_PATH"
    echo "Applying migrations..."
    (cd "$PROJECT_ROOT" && $ALEMBIC_CMD upgrade head)
    echo "Database migrations applied successfully!"
fi
