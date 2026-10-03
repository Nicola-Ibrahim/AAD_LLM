# Independent analysis workflows

[Project README](../../README.md) · [Documentation map](../../docs/README.md) ·
[Evaluation protocol](../../docs/evaluation_protocol.md)

Run any of these notebooks without running the others first:

| Notebook | Workload |
| --- | --- |
| [05_reliability_summary.ipynb](05_reliability_summary.ipynb) | Native reliability tables and the fixed-target attainment PNG. No adaptive AUC or cross-function loading. |
| [06_convergence_ecdf_and_ablations.ipynb](06_convergence_ecdf_and_ablations.ipynb) | Exploratory AUC summaries, strategy ablations, explicit/implicit convergence and ECDF profiles. Run selected sections; PNG sweeps can be slow. |
| [07_noise_robustness.ipynb](07_noise_robustness.ipynb) | Success rate versus noise with condition-bootstrap intervals. No ECDF or cross-function exports. |

Each notebook discovers the project root and calls injected application use cases.
The use cases load completed DB models, current champion identities, validated
provenance and available traces, then call domain engines. No evaluation or
synthesis campaign is launched.

The backend has no Plotly dependency or figure-export code. Application modules
in `src/benchmarking/application/analysis/` coordinate profile, reliability,
noise-robustness and performance analysis; domain engines own the scientific calculations. Notebook-owned
helpers handle visual layout, styling and explicit PNG export, without figure caching.
The infrastructure `AnalysisResultsStore` saves calculated arrays and statistics;
it never queries experiments or invokes analysis engines.
The helper modules are grouped by workflow: `summary.py`, `performance.py`,
`profiles.py`, and `generalization.py`, with shared `style.py` and `exporter.py`.

Use cases return typed calculated results: no live database repository, raw dataset
or engine service is carried into plotting. Helpers consume arrays and tables,
never call scientific engines. Profiles exclude
stale champion identities; completed terminal trials do not imply that all their
convergence traces are available.

Calculation and export are separate notebook cells. Required collaborators are
constructed by bootstrap, not by optional constructor fallbacks:

```python
from bootstrap.analysis import build_analysis_use_cases
with build_analysis_use_cases() as analysis:
    profiles = analysis.ecdf_and_convergence.execute(
        mode="explicit",
        dims=[2],
        problems=None,
        noise_stds=[0.05, 0.1, 0.2],
    )
```

At this point no images or CSVs have been written. Inspect `profiles.conditions`,
then run the optional export cell:

```python
from bootstrap.analysis import build_analysis_results_store
from notebooks.analysis.plotting.exporter import AnalysisFigureExporter
from shared.config import RESULTS_DIR

store = build_analysis_results_store()
snapshot_path = store.save(profiles)
exporter = AnalysisFigureExporter(RESULTS_DIR)
exporter.export_profiles(profiles)
```

For an individual figure, call `build_profile(condition, profiles.mode,
kind="ecdf", title="...")` and pass its returned figure and output path to
`exporter.export_figure(figure, output_path)`.
The context manager disposes the database; calculated arrays and tables remain
usable afterward. Treat result arrays/tables as read-only. `None` in condition
filters means unrestricted; required constructor dependencies never default to it.

There are no request wrapper classes: use cases accept explicit keyword parameters.
`data_loader.py` owns loading and its internal snapshot; the four `analyze_*.py`
modules own independently runnable workflows. `results.py` keeps the
typed return values consumed by plotting.

`AnalyzeEcdfAndConvergence` calculates both convergence (median and IQR) and
adaptive-target ECDF curves in one pass over their shared interpolated traces.
Access it through `analysis.ecdf_and_convergence.execute(...)`. Keeping these
calculations together avoids duplicate loading and interpolation. Statistical
calculations and CSV exports remain available; unused Markdown report export
components have been removed.

The retained ECDF engine computes paired profiles or ECDF-only curves for AUC;
AUC no longer calculates discarded median/IQR statistics. Performance calculations
retain model-scale/AUC summaries and function-hardness success rates. Retired
aggregate profiles and legacy figure-specific metrics are no longer exposed.
Current output names, series, targets and scientific formulas are unchanged.

Each calculation cell saves numeric results under `results/analysis/`: compressed
NPZ arrays for ECDF, convergence, targets and confidence bands; CSV tables for
statistics; and a versioned JSON manifest for identities, diagnostics, provenance
and artifact checksums. Profile snapshots are grouped by explicit/implicit/comparison
mode. Content-addressed folders preserve earlier calculations rather than replacing
them. The printed snapshot path identifies the exact result.

To reuse a snapshot after a kernel restart, skip calculation and load its printed path:

```python
profiles = store.load(store.root / "profiles" / "explicit" / "<printed-signature>")
AnalysisFigureExporter(RESULTS_DIR).export_profiles(profiles)
```

Snapshots are detached, validated on reload, and do not automatically incorporate
new evaluations. Rerun calculation when source results change.
The exporter also exposes `export_reliability`, `export_noise_robustness`,
`export_model_scale`, and `export_hardness_ablation`.
Figures and established report CSVs remain under `results/figures/` and
`results/reports/`. Images are PNG-only, high-resolution, and never rendered inline.
Classical baseline profiles are solid; LLM profiles are dashed. The explicit-versus-
implicit comparison intentionally distinguishes informed/blind modes by line style.

The optional `FILTER_DIMS`, `FILTER_PROBLEMS` and `FILTER_NOISE_STDS` settings
reduce work. Only intermediate arrays, statistics and their provenance are saved
for reuse. Plotly objects, PNGs and image-export status are never cached.
Each explicit export call rebuilds the figures from calculated results and writes
the requested PNGs, replacing existing files at the established output paths.
Changing styling requires only another export, not recalculation.

The legacy combined figures notebook has been retired. Use the three notebooks
in this folder; there is no forwarding notebook or duplicated plotting code.
