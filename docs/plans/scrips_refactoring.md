# Refactor: CLI Scripts Architecture

The goal is to rethink and refactor the `scripts/` directory to separate concerns, consolidate related operations, and maintain safety for destructive actions.

## User Review Required

> [!IMPORTANT]  
> Please review the proposed separation of concerns below. This refactoring will merge the LLM scripts and split the cleanup logic out of the database script. Does this align with how you prefer to manage the project?

## Proposed Changes

We will refactor the four existing scripts into a more cohesive hierarchy.

---

### LLM Scripts Consolidation

Currently, model downloading/listing (`llm_manage.sh`) and model serving (`llm_server.sh`) are separated, but they share significant context (Python resolution, Hugging Face cache paths, environment variables).

#### [DELETE] `scripts/llm_manage.sh`
#### [DELETE] `scripts/llm_server.sh`
#### [NEW] `scripts/llm.sh`
We will create a unified `llm.sh` script with the following commands:
- `start` / `stop` / `status` (from `llm_server.sh`)
- `download` / `cleanup` / `list` (from `llm_manage.sh`)

This reduces duplicated boilerplate (e.g., Python path resolution, interactive menus, `print_header`) and provides a single entry point for all LLM-related tasks.

---

### Database and Artifact Separation

Currently, `db.sh clear` and `db.sh reset` manage SQLite operations but also prompt to delete file artifacts (`data/evolution_state`, `data/code`, `data/ioh_logs`). This violates the single responsibility principle.

#### [MODIFY] `scripts/db.sh`
- Keep all Alembic migration commands (`upgrade`, `rollback`, `revision`, `both`, `status`).
- Keep `clear` (truncate all tables) and `reset` (delete and recreate DB file).
- **Remove** the prompts and logic that delete `evolution_state`, `code`, and `ioh_logs` from this script. `db.sh` will strictly manage the SQLite database.

#### [NEW] `scripts/clean.sh`
Create a dedicated cleanup script for managing file artifacts.
- Incorporates the user's preferred `confirm` and `confirm_type` safety checks.
- Focuses purely on `data/evolution_state`, `data/code`, `data/ioh_logs`, and potentially `logs/`.

---

### Environment Setup

#### [MODIFY] `scripts/env.sh`
- Keep mostly as-is. It remains the dedicated script for `uv`/`pip` installation, `.venv` management, and CUDA/Metal GPU detection.
- We just need to update any references inside to point to `scripts/llm.sh` instead of `scripts/llm_server.sh`.

## Verification Plan

### Manual Verification
- Run `bash scripts/llm.sh` to verify the interactive menu works.
- Run `bash scripts/db.sh clear` and verify it only prompts for DB deletion, not artifacts.
- Run `bash scripts/clean.sh` and verify file cleanup works safely with confirmations.
