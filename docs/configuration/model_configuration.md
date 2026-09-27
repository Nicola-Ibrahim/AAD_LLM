# Model configuration

[Documentation map](../README.md) · [Project README](../../README.md)

Provider connections, server settings, model presets and experimental settings
have different owners; model selection is not entirely configuration-free.

## Provider connections

[LLMClient](../../src/evolution/infra/llm/client.py) supports `local`, `lmstudio`
and `gemini`. The notebook supplies the provider and optional client arguments.
Environment variables provide defaults:

| Provider | URL | Model | API key |
| --- | --- | --- | --- |
| Local | `LOCAL_LLM_BASE_URL` | `LOCAL_LLM_MODEL` | `LOCAL_LLM_API_KEY` |
| LM Studio | `LLM_STUDIO_BASE_URL` | `LLM_STUDIO_MODEL` | `LLM_STUDIO_API_KEY` |
| Gemini | Provider-managed | `GEMINI_MODEL` | `GOOGLE_API_KEY` |

Local and LM Studio default to `http://localhost:1234/v1`.
An explicit `model=` argument takes precedence over the model environment variable.
With connection validation enabled and no configured model, the client discovers
the first model returned by the endpoint's `/models` response. With validation
disabled, a model must be supplied. `SKIP_LLM_VALIDATION=True` disables the
connection probe; it is not a substitute for configuring the model.
Keep API keys in local environment configuration, not committed documents.

## Local GGUF server

The existing management script supports:

```bash
bash scripts/llm.sh start
bash scripts/llm.sh status
bash scripts/llm.sh stop
bash scripts/llm.sh download
bash scripts/llm.sh list
bash scripts/llm.sh cleanup
```

Running `bash scripts/llm.sh` opens its interactive menu. Starting the server
selects an available GGUF file; downloading offers presets or a custom repository
and file. `cleanup` deletes selected model files and should be used deliberately.

Server settings include `LLM_SERVER_HOST`, `LLM_SERVER_PORT`,
`LLM_SERVER_N_CTX`, `LLM_SERVER_N_THREADS`, `LLM_SERVER_N_GPU_LAYERS`
and `LLM_SERVER_VERBOSE`. `MODELS_DIR` overrides the default model directory
`~/models`. Server bind settings and Python client URLs are separate: if the
port changes, update the corresponding client base URL too. A bind address such
as `0.0.0.0` is not the client connection URL.

## Presets and experiments

[configs/llms.toml](../../configs/llms.toml) stores model presets/registry metadata;
it is used by the management tooling and infrastructure name registry.
It does not declare which models have completed experiments.

[configs/synthesis.toml](../../configs/synthesis.toml) controls problem conditions,
prompt strategies, synthesis modes, iterations and future repeat counts.
[configs/benchmark.toml](../../configs/benchmark.toml) controls evaluation and
reliability settings. Audit and analysis discover completed models from the
database rather than treating every registry preset as an evaluated model.

### Selective synthesis reruns

Keep protocol settings in `synthesis.toml`; pass selections to each campaign call:

```python
# Automatic recovery only, for the active LLM:
campaign_usecase.run_campaign(recover=True)

# Recovery plus manually selected conditions (review IDs for the current DB):
campaign_usecase.run_campaign(
    recover=True,
    rerun_experiment_ids=[2091, 2737, 2147],
    rerun_repeats=1,
)

# Resume specific running sessions, without scheduling other work:
campaign_usecase.run_campaign(resume_experiment_ids=[123])

# Fill the full configured matrix to its replicate target:
campaign_usecase.run_campaign()
```

Use the matching model server. These options are invocation-scoped: changing IDs
does not require editing TOML or restarting the kernel. After updating Python
code, restart Notebook 02's kernel. The planner
combines manual conditions with configured-matrix recovery for the active model:
interrupted sessions are resumed when `auto_resume` is enabled, and unresolved
synthesis failures receive one fresh attempt when `retry_failed_synthesis` is
enabled, but only when the condition has no completed valid champion. Any completed
valid champion satisfies automatic recovery, even if individual candidate iterations,
other sessions, or leftover queued records failed. Historical records
remain unchanged. Multiple selected IDs for one condition are deduplicated, and
pending sessions fill manual repair slots rather than creating duplicate runs.
`rerun_repeats`, not `runs_per_config`, sets the manual slots. This recovery path
does not expand unrelated conditions into extra replicates. Unknown IDs are rejected;
`resume_experiment_ids` cannot be combined with recovery or fresh reruns, and only
running records belonging to the active LLM are resumed. No audit workflow is required.
Each call rediscovers database state. Automatic recovery needs no manual IDs.
Logs show only `Exp ID`, the actual executing database record: fresh attempts
receive a new ID, while resuming retains its existing ID. Manual IDs identify
source conditions and are not substituted for the executing record's ID.
Omit manual IDs after successful repairs: explicitly passing them again requests
another fresh repeat, unless interrupted sessions already fill the slots. The
matrix audit measures conditions with a completed valid champion, not the fraction
of successful candidate iterations. Running/failed record counts remain visible
as history without making a covered condition incomplete. A valid champion means
finite synthesis error, not guaranteed success on the independent benchmark.

The standard protocol has `iterations = 10` candidate generations in one synthesis
session and `runs_per_config = 1` session per condition. These are different counts.
Only deliberately increase `runs_per_config` for a separate replicate campaign.
Poor benchmark results may motivate explicit rerun IDs; they do not automatically
invalidate a completed synthesis session or change champion-ranking mathematics.

Imported databases can use different IDs. Review and refresh the selection after
an import. New synthesis does not guarantee that champion selection will change:
the existing synthesis-error/evaluation-count ranking remains unchanged, and
benchmark outcomes are not used to rank candidates. Additional search motivated
by benchmark feedback must be documented as a follow-up campaign, not silently
substituted into the original thesis results.

Quantization labels identify model artifacts; they do not establish guaranteed
memory requirements, runtime or optimization quality. Report the exact model
artifact and actual experimental settings when comparing results.
