# Clarify the Aggregate Boundary: ExperimentHeader + ExperimentSummary

## Background

After the previous discussion we established that the codebase has a legitimate architectural
tension: the experiment DB row must exist *before* the loop starts (for crash-recovery), but
canonical DDD says "create the entity fully, then persist it."

The root cause is that `ExperimentSummary` currently plays **two conflicting roles**:

| Role | Used for | Lifecycle |
|---|---|---|
| **Write model** | `create_experiment` needs scalars, not a built entity | Born before the loop |
| **Read model** | `repo.load()` returns fully-populated `ExperimentSummary` objects | Born after the loop |

Clarifying the boundary removes the ambiguity without breaking anything.

---

## What Changes

### Concept Map (Before → After)

```
BEFORE
──────
session._init_experiment_context()
  → repo.create_experiment(scalars) → int (bare ID)
  → evaluator carries that int as self._experiment_id
  → experiment_meta: dict[str,Any] passed around as raw dict

AFTER
─────
session._init_experiment_context()
  → builds ExperimentHeader (small entity: mode, llm_name, problem, prompt_strategy)
  → repo.register(header) → header with id assigned
  → evaluator carries ExperimentHeader (typed, no dict)
  → repo.append_iteration(experiment_id, metadata) unchanged
  → repo.load() still returns list[ExperimentSummary] (read model, unchanged)
```

---

## Proposed Changes

### Domain Layer

#### [MODIFY] [experiment.py](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/src/core/domain/experiment.py)

**Add** `ExperimentHeader(DomainEntity)` — the minimal **write-side entity** that is created
at session startup and passed to the repo:

```python
class ExperimentHeader(DomainEntity):
    """Minimal entity created at session startup to register an experiment run.

    This is the write-side representation. It carries only the fields needed to
    open an experiment row in the DB. Once the run completes, the full read-side
    summary is reconstructed via repo.load() as ExperimentSummary.
    """
    mode: str
    llm_name: str
    prompt_strategy: str
    problem: ProblemProfile
    status: str = "running"
    started_at: str | None = None
```

> **Note:** `ExperimentSummary` remains unchanged. It is the **read model** — populated
> only by `repo.load()`. No changes needed there.

#### [MODIFY] [\_\_init\_\_.py](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/src/core/domain/__init__.py)

Export `ExperimentHeader` alongside `ExperimentSummary`.

---

### Repository Interface

#### [MODIFY] [base.py](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/src/infra/storage/base.py)

Replace `create_experiment(scalars…) -> int` with `register(header: ExperimentHeader) -> ExperimentHeader`:

```python
@abstractmethod
def register(self, header: ExperimentHeader) -> ExperimentHeader:
    """Persists a new experiment header row and returns the same object with id assigned."""
    pass
```

The return type is `ExperimentHeader` (not `int`) so the caller gets a typed, id-bearing
object back — not a bare integer. The caller then reads `header.id` when needed.

> `append_iteration`, `mark_completed`, `mark_failed`, `get_experiment_status`,
> `get_incomplete_experiments`, `load`, `checkpoint_wal`, `get_best_raw_fitness` — all
> **unchanged**.

---

### Repository Implementation

#### [MODIFY] [repository.py](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/src/infra/storage/sqlite/repository.py)

Replace the `create_experiment` implementation with `register(header) -> ExperimentHeader`:

```python
def register(self, header: ExperimentHeader) -> ExperimentHeader:
    with Session(self._engine) as session:
        row = ExperimentORM(
            problem_id=header.problem.problem_id,
            instance_id=header.problem.instance_id,
            dim=header.problem.dim,
            mode=header.mode,
            llm_name=header.llm_name,
            noise_std=header.problem.noise_std,
            true_optimum=header.problem.true_optimum,
            prompt_strategy=header.prompt_strategy,
            status=header.status,
            started_at=header.started_at,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        # Return the same VO with id populated (model_copy preserves immutability pattern)
        return header.model_copy(update={"id": row.id})
```

---

### Service Layer

#### [MODIFY] [session.py](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/src/core/llamea/session.py)

`_init_experiment_context` builds an `ExperimentHeader`, calls `repo.register()`, and stores
the returned header instead of a bare int:

```python
def _init_experiment_context(self, resume_experiment_id: int | None) -> None:
    if resume_experiment_id is not None:
        # Resume path: unchanged, still uses get_experiment_status + get_incomplete_experiments
        status, max_iter = self._db_repo.get_experiment_status(resume_experiment_id)
        ...
        self._initial_iteration = max_iter
        self._experiment_header = ExperimentHeader(
            id=resume_experiment_id,
            mode=self._problem.mode,
            llm_name=self._llm_client.model.name,
            prompt_strategy=self._prompt_strategy,
            problem=ProblemProfile(...),
        )
    else:
        self._initial_iteration = 0
        header = ExperimentHeader(
            mode=self._problem.mode,
            llm_name=self._llm_client.model.name,
            prompt_strategy=self._prompt_strategy,
            problem=ProblemProfile(
                problem_id=self._problem.problem_id,
                instance_id=self._problem.instance_id,
                dim=self._problem.dim,
                noise_std=self._problem.noise_std,
                true_optimum=self._problem.true_optimum,
            ),
        )
        self._experiment_header = self._db_repo.register(header)
```

Replace all usages of `self._experiment_id` → `self._experiment_header.id`.

#### [MODIFY] [evaluator.py](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/src/core/llamea/evaluator.py)

Replace `experiment_id: int` + `experiment_meta: dict` constructor parameters with a single
`header: ExperimentHeader` parameter:

```python
def __init__(
    self,
    problem: BBOBProblem,
    db_repo: ExperimentRepository,
    code_repo: CodeRepository,
    budget: int = 1000,
    timeout_seconds: float = 10.0,
    header: ExperimentHeader = ...,     # replaces experiment_id + experiment_meta
    initial_iteration: int = 0,
) -> None:
    ...
    self._header = header
    self._experiment_id = header.id     # convenience alias for repo calls
```

The `experiment_meta` dict is deleted entirely — everything it carried is already on `header`.

---

## Verification Plan

### Automated Tests
```bash
uv run pytest
```
All existing tests should pass without modification (the only changed public surface is
`create_experiment` → `register` on the repo, and `experiment_id + experiment_meta` →
`header` on the evaluator).

### Manual Check
- Confirm `session.py` no longer uses a bare `int` for experiment identity.
- Confirm `evaluator.py` no longer accepts or stores `experiment_meta: dict`.
- Confirm `ExperimentSummary` is untouched (read model, repo.load() still works).

---

## What This Does NOT Change

| Thing | Stays the same |
|---|---|
| `ExperimentSummary` read model | ✅ Unchanged |
| `repo.load()` signature | ✅ Unchanged |
| `repo.append_iteration()` | ✅ Unchanged |
| `repo.mark_completed/failed()` | ✅ Unchanged |
| DB schema / ORM tables | ✅ Unchanged |
| The durability-first design | ✅ Unchanged — header is still registered before loop starts |

The only architectural shift is that the **coordination token** between session → evaluator → repo
is now `ExperimentHeader` (a typed domain object) instead of a raw `int` + untyped `dict`.
