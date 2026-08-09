# IOHanalyzer Integration Plan (Final)

## Goal
Integrate IOHanalyzer into the experimental pipeline so that LLM-generated algorithm results can be fairly and rigorously compared against classical baseline optimizers (CMA-ES, DE, PSO) using standardized BBOB benchmarking figures.

---

## Locked-In Decisions

| Parameter | Value | Source |
|---|---|---|
| Target BBOB problems | `f1, f8, f11, f15, f21` | User confirmed |
| Noise level | `noise_std = 0.05` (CV) | User confirmed |
| Dimensionality | `dim = 5` | Existing setup |
| Noise model | `MultiplicativeNoiseStrategy` | Existing codebase |
| Baseline algorithms | CMA-ES, DE, PSO | Professor requirement |
| IOH `raw_y` = `Δf = f_clean - f_opt` | ✅ Verified via live code experiment | — |
| Logger fires before noise | ✅ Verified via live code experiment | — |

---

## Critical Design: Two-Phase Experimental Protocol

This distinction is the most important architectural decision in the plan.

### Phase A — Training Phase (LLaMEA Discovery)
LLaMEA runs its evolutionary synthesis loop. Each iteration produces a candidate algorithm and runs it for `budget` evaluations on the noisy problem. The IOH logger records the per-step clean trajectory for *every evaluation during training*.

However, **training trajectories are NOT used directly for comparison**. They represent different algorithms at different evolutionary stages — comparing these against a fixed baseline algorithm (CMA-ES run 10 times) would be apples-to-oranges.

### Phase B — Evaluation Phase (Champion Assessment)
After all training is complete, the **best algorithm code** discovered by LLaMEA (the champion) is extracted and run independently `N = 10` times on each target problem. These 10 independent runs form the IOHanalyzer data for "LLaMEA Champion on f8".

Baselines (CMA-ES, DE, PSO) are also run `N = 10` independent times under identical conditions.

> This is the standard approach in AAD literature and ensures every algorithm is evaluated with the same number of independent stochastic trials.

```
TRAINING PHASE (LLaMEA Discovery)          EVALUATION PHASE (Champion Assessment)
─────────────────────────────────          ──────────────────────────────────────
LLaMEA Experiment #1 on f8                Champion Code → Run 1 on f8   ─┐
  Iter 1: AlgoA  (B evals) ─┐                                Run 2 on f8   │
  Iter 2: AlgoB  (B evals)  │ IOH .dat    CMA-ES             Run 3 on f8   │──► IOHanalyzer
  Iter 3: AlgoC  (B evals) ─┘ (training) Champion → ...      ...           │    ECDF / ERT
  ...                                                         Run 10 on f8  │
LLaMEA Experiment #2 on f8                                                 ─┘
  ...
    ↓
 Select champion: lowest final_error
 across ALL experiments for f8
```

---

## LLaMEA Champion Selection Policy

> [!IMPORTANT]
> Multiple LLaMEA experiments may exist for the same `(problem_id, noise_std)`. The selection rule must be defined unambiguously.

**Rule**: For each `(problem_id, noise_std)` pair, the champion is the algorithm with the **lowest `final_error` across all iterations across all experiments** for that pair, filtered to `status = 'completed'` only.

**Balancing requirement**: All 5 target problems (`f1, f8, f11, f15, f21`) must have the **same number of completed LLaMEA experiments** before final champion selection. If problem `f8` has 3 completed experiments but `f11` only has 1, run 2 more experiments for `f11` before selection.

This balancing ensures that LLaMEA's champion discovery is not biased by giving more evolutionary attempts to some problems than others.

#### [NEW] `scripts/select_champions.py`
A CLI script that:
1. Queries SQLite for all `completed` experiments per problem at `noise_std=0.05`.
2. Reports the current balance table (experiments per problem).
3. If balanced: extracts the `code_path` of the best iteration per problem.
4. Outputs a `data/champions.json` mapping `problem_id → code_path + metadata`.

```bash
uv run python scripts/select_champions.py --noise_std 0.05 --check-balance
# Output: balance table + warnings for any under-represented problems
```

---

## Proposed Code Changes

---

### Phase 1 — Attach IOHLogger to `BBOBProblem`

#### [MODIFY] `src/infra/problems/bbob.py`
- Add optional `ioh_logger: ioh.logger.Analyzer | None = None` parameter to `__init__`.
- If provided: `self._clean_problem.attach_logger(ioh_logger)` — one line.
- The logger auto-fires on every `_clean_problem(x)` call, recording `(evaluations, Δf_clean)` to `.dat`, **before noise is applied**.
- `__setstate__` (unpickle resume) must store the logger reference and re-attach it.

**This is the only change needed for trajectory logging. Noise logic, evaluator, and SQLite are untouched.**

#### [MODIFY] `src/synthesis/session.py`
- `LLaMEASession.create()` builds an `ioh.logger.Analyzer` pointing to:
  `data/ioh_logs/f{problem_id}_{dim}D_std{noise_std}/{llm_name}_exp{experiment_id}/`
- Logger `algorithm_name` = `"{llm_name}_{prompt_strategy}"` for correct IOH metadata.
- The logger is passed into `BBOBProblem` on construction.

---

### Phase 2 — Champion Evaluation Script

#### [NEW] `scripts/evaluate_champions.py`
Reads `data/champions.json`, loads each champion's code, and runs it `N=10` independent times on its target problem with `IOHLogger` attached. Trajectories are written to:
`data/ioh_logs/f{problem_id}_{dim}D_std{noise_std}/llamea_champion/`

```bash
uv run python scripts/evaluate_champions.py \
    --champions data/champions.json \
    --n_runs 10 \
    --budget 100000
```

---

### Phase 3 — Baseline Algorithm Runner

#### [NEW] `scripts/run_baselines.py`
Runs CMA-ES, DE, PSO `N=10` times per problem under the **exact same noisy `BBOBProblem`** wrapper. Trajectories written to:
`data/ioh_logs/f{problem_id}_{dim}D_std{noise_std}/{algorithm_name}/`

```bash
uv run python scripts/run_baselines.py \
    --problem_ids 1 8 11 15 21 \
    --dim 5 \
    --noise_std 0.05 \
    --algorithms cmaes de pso \
    --n_runs 10 \
    --budget 100000
```

Algorithms:
- **CMA-ES**: `cma` Python library, ~30 lines, budget-limited loop.
- **DE**: `scipy.optimize.differential_evolution` with budget callback.
- **PSO**: lightweight vectorized implementation, ~50 lines.

> [!IMPORTANT]
> Each baseline receives `f_noisy` from `BBOBProblem.__call__()` — identical to what LLaMEA algorithms see. The IOH logger records `f_clean - f_opt` in parallel. This is the only scientifically valid comparison setup.

---

### Phase 4 — Update Notebooks

#### [MODIFY] `notebooks/03_results_analysis.ipynb`
- Add section: **IOHanalyzer Comparison (Champion vs Baselines)**.
- Load `data/ioh_logs/` with `iohanalyzer` Python package.
- Generate ECDF, fixed-budget curves, ERT tables.

#### [NEW] `notebooks/04_ioh_comparison.ipynb`
- Dedicated thesis-figure notebook.
- Outputs `.pdf`/`.pgf` to `writing/thesis/figures/`.
- One figure per problem group: separable (f1), moderate conditioning (f8), multi-modal (f11, f15, f21).

---

### Phase 5 — New Tests

#### [MODIFY] `tests/test_bbob_scalar.py`
- `test_ioh_logger_records_clean_distance`: attach logger to noisy problem, confirm `.dat` `raw_y` = `f_clean - f_opt`, not `f_noisy - f_opt`.
- `test_ioh_logger_noisy_problem_does_not_corrupt_trajectory`: verify that `MultiplicativeNoiseStrategy` being active has zero effect on logger output.

---

## Verification Checklist

> [!IMPORTANT]
> Every item below must be verified before the comparison is presented in the thesis.

| Check | How to verify | Status |
|---|---|---|
| IOH `raw_y` = `f_clean - f_opt` | ✅ Confirmed via live code experiment | Done |
| Logger fires before noise, not after | ✅ Confirmed via live code experiment | Done |
| All 5 problems have equal experiment counts | `select_champions.py --check-balance` | Pending |
| Champion selected by lowest `final_error` across all experiments | Code review of `select_champions.py` | Pending |
| Champion runs N=10, baselines run N=10 | Code review | Pending |
| Baselines receive same noisy objective as LLM algorithms | Code review of `run_baselines.py` | Pending |
| Same `noise_std=0.05` and `noise_model` across all runs | Same `BBOBProblem` constructor | Pending |
| Same `budget` across champion + baseline evaluation runs | Same `budget` parameter | Pending |
| Same `instance_id=1` across all runs | Code review | Pending |
| IOH `.dat` files from all algorithms overlay cleanly in IOHanalyzer | Upload test set to web app | Pending |

---

## Final Directory Structure After Integration

```
data/
└── ioh_logs/
    ├── f1_5D_std0.05/
    │   ├── llamea_champion/           ← 10 independent runs of best LLaMEA code
    │   ├── cmaes/                     ← 10 independent CMA-ES runs
    │   ├── de/                        ← 10 independent DE runs
    │   └── pso/                       ← 10 independent PSO runs
    ├── f8_5D_std0.05/
    │   └── ...
    ├── f11_5D_std0.05/
    │   └── ...
    ├── f15_5D_std0.05/
    │   └── ...
    └── f21_5D_std0.05/
        └── ...
```

---

## Implementation Order

```
Phase 1 (BBOBProblem logger + session.py, ~2 hrs)
   └─► Phase 5 (new tests, ~1 hr)
         └─► Phase 2 (select_champions.py, ~2 hrs) ── requires balanced training data
               ├─► Phase 3 (evaluate_champions.py, ~2 hrs)
               ├─► Phase 3 (run_baselines.py, ~1 day)
               └─► Phase 4 (notebooks + thesis figures, ~1 day)
```

Total estimated effort: **~3-4 focused working days** (excluding LLaMEA re-training time to balance experiments).
