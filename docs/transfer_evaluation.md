# Noise robustness and cross-function generalization

These are separate secondary questions. Neither enters the native champion ranking.

## Native performance

Select a champion using its synthesis condition, then evaluate it on the original
function and dimension. Terminal reliability uses the **returned point**:

`gap = max(0, target_clean_objective(returned_x) - target_optimum)`.

The primary solved threshold is `1e-8`; the secondary threshold is `1e-2`.
Clean convergence traces instead describe the best clean point queried during
search. Attainment of a queried point does not prove that the optimizer returned
that point. ECDFs use observed attainment times, without interpolating a success
between observations.

## Noise robustness

`service.run_noise_robustness()` freezes each clean explicit champion and tests
added noise on its original function and dimension. The existing
`cross_eval_clean_champions` configuration key enables/disables this workflow.
Historical storage remains `results/ioh_traces/`; it is not moved or deleted.
Notebook 07 requires matching clean-champion code hashes across noise levels and
excludes separately synthesized noisy and implicit champions from these overlays.
Its robustness ECDFs use the same fixed target set across noise levels; adaptive
targets remain exploratory elsewhere. Figures use `results/figures/05_noise_robustness/`.

## Cross-function generalization

Enable `benchmarking.cross_function_enabled` in `configs/benchmark.toml`, then set
`RUN_CROSS_FUNCTION = True` in notebook 03's separate campaign cell, or explicitly
call `service.run_cross_function_evaluations()`.

Only clean, explicit, baseline-strategy champions enter this workflow. Their code
is unchanged, their dimension is unchanged, and the clean target functions default
to f1, f8, f11, f15 and f21. Diagonal source–target cells provide native-function
references, reused from the ordinary native trace folders when current. Off-diagonal
cells measure transfer, not a replacement native ranking.
No champion is selected or tuned using transfer results. Classical CMA-ES, DE and
PSO results are evaluated once per target condition in their ordinary trace
folders and reused across source-function comparisons.

Off-diagonal transfer results live separately in `results/cross_function_traces/`, grouped by
source function, dimension, target noise, target function, model/strategy and code
hash. Provenance records both source and target identities, champion experiment
and iteration, code hash, instances, seeds, budgets and returned-point errors.
Resumption requires the current code hash and error schema. Noise/native folders
and transfer folders cannot overwrite each other.

Notebook 07 (`notebooks/analysis/07_generalization.ipynb`) reads transfer results
matching current database-selected champions. It runs independently of the primary
analysis notebook and the detailed performance-profile notebook.
It exports source–target PNG matrices to `results/figures/07_cross_function/` and
versioned condition/aggregate CSVs to `results/reports/`, without displaying PNGs
inline or writing HTML figures. Missing and incomplete cells are grey and excluded
from aggregate estimates. Aggregate scores weight complete off-diagonal conditions
equally; deterministic bootstrap intervals resample conditions, not pooled trials.

## Interpretation and historical trials

All workflows retain the existing dimension-scaled budgets, timeout, trial count,
paired instance IDs 1–20 and seeds derived from the configured base seed. Because
the synthesis instance is included, this is not exclusively held-out-instance
evaluation. Baselines are general-purpose references; generated champions were
selected for their source problem. Poor transfer can therefore demonstrate
specialization without contradicting strong native performance.

Every scheduled trial now executes even after earlier failures. Historical
infinite-error tails with zero runtime and zero evaluations from the old
two-failure shortcut are unexecuted, not empirical failures. Readiness and terminal
analysis exclude those tails, and subsequent evaluation resumes them while keeping
the genuine earlier trials. No existing results are rewritten by analysis alone.
