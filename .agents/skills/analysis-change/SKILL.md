---
name: analysis-change
description: Change AAD_LLM ECDF, convergence, reliability, statistical analysis or notebook plotting while preserving scientific meaning and presentation contracts.
---

# Change analysis and presentation

Inputs: the metric/presentation question or requested change, affected use case,
domain engine and its notebook/figure builder. Read only the path needed for the
request; a styling-only task does not require unrelated statistical engines.
Use [research-change](../research-change/SKILL.md) for substantial-task phases and records.

## Establish the affected scientific contract

Read the affected application analysis use case and domain engine, then its notebook
and figure builder as relevant. Consult [benchmark protocol](../../../docs/benchmark_protocol.md)
and [analysis guide](../../../notebooks/analysis/README.md) for the relevant metric.

Trace eligibility and data flow separately from arithmetic: current champion hashes,
terminal completeness, trace availability, native/frozen/transfer scope, failures
and missing observations. Record what enters each denominator. Defaults are not
evidence of the parameters used by historical benchmark records.

## Apply the relevant branch

**If scientific behavior or its implementation changes:** characterize the affected outputs using synthetic or
existing isolated fixtures: best-so-far/carry-forward, interpolation grids, targets,
median/IQR, AUC integration, thresholds, Wilson intervals, bootstrap seed/count/order
and condition weighting. Keep adaptive-target ECDF distinct from fixed-target
attainment and returned-solution success. Change definitions only with authorization.

For all analysis code, keep these boundaries:

Application use cases load through injected collaborators and return calculated
arrays/tables plus metadata. Domain engines own mathematics. Notebook figure
builders consume calculated results; they do not load traces or compute statistics.
Numerical snapshot storage, CSV export and figure export remain explicit operations.

**If presentation changes:** preserve full model names, consistent strategy colors,
LLM/baseline line styles, filenames and PNG-only export unless requested otherwise.
Check figures from precomputed fixtures when useful. Preserve notebook outputs and
existing images; do not execute export or regenerate study results just to check code.
Use [research-verification](../research-verification/SKILL.md) to select and safely
execute checks covering the affected contract; it owns isolation and commands.
Use [research-storage](../research-storage/SKILL.md) when changing snapshot
serialization or provenance selection.

## Output and stopping point

For review/planning, return metric definitions, denominator/eligibility findings,
risks and proposed checks in chat or the permitted task record; stop before code
edits or calculations/exports outside the authorized planning scope. For authorized implementation,
produce the scoped analysis/presentation changes and a verification summary for
research-change's handoff when applicable. Export figures, CSVs or calculated study
results only when explicitly within scope; otherwise stop with code/fixture checks.
