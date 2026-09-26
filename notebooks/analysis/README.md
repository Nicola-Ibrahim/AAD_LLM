# Independent analysis workflows

Run any of these notebooks without running the others first:

| Notebook | Workload |
| --- | --- |
| [05_analysis.ipynb](05_analysis.ipynb) | Native reliability tables and three primary thesis PNGs. No adaptive AUC or cross-function loading. |
| [06_performance_profiles.ipynb](06_performance_profiles.ipynb) | Exploratory AUC summaries, strategy ablations, explicit/implicit convergence and ECDF profiles. Run selected sections; PNG sweeps can be slow. |
| [07_generalization.ipynb](07_generalization.ipynb) | Frozen-champion noise overlays and separate cross-function transfer matrices/CSVs. Run either export section independently. |

Each notebook discovers the project root, reads completed DB models and current
champion identities, and loads its own inputs. No evaluation or synthesis campaign
is launched. Calculations remain in domain engines; shared Plotly styling and
builders are in `notebooks/analysis/plotting/`.

The backend has no Plotly dependency or figure-export code. Application modules
in `src/benchmarking/application/analysis/` prepare analysis inputs and exploratory
performance metrics; domain engines own the scientific calculations. Notebook-owned
helpers handle visual layout, styling, CSV exports, PNG saving, and figure caching.
The helper modules are grouped by workflow: `summary.py`, `performance.py`,
`profiles.py`, and `generalization.py`, with shared `style.py` and `cache.py`.

Analysis inputs are data snapshots: no live database repository or engine service
is carried into plotting. Helpers call domain engines directly. Profiles exclude
stale champion identities; completed terminal trials do not imply that all their
convergence traces are available.

Outputs remain under the established `results/figures/` and `results/reports/`
locations. Images are PNG-only, high-resolution, and never rendered inline.
Classical baseline profiles are solid; LLM profiles are dashed. The explicit-versus-
implicit comparison intentionally distinguishes informed/blind modes by line style.

The optional `FILTER_DIMS`, `FILTER_PROBLEMS` and `FILTER_NOISE_STDS` settings
reduce work. Keep `FORCE_EXPORT = False` for normal use. Each successful image is
checkpointed immediately in its workflow's manifest under
`results/reports/.analysis_cache/`; interrupted sweeps can resume. Cache signatures
include relevant source data, configuration, filters and plotting/scientific code.
Transfer-result changes do not invalidate the primary/profile/noise caches.

The original combined `notebooks/05_analysis.ipynb` has been replaced by this folder;
there is no forwarding notebook or duplicated plotting code.
