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

Add experiment IDs to the `[execution]` section of `synthesis.toml`:

```toml
rerun_experiment_ids = [2091, 2737, 2147] # Example: current DeepSeek database IDs
rerun_repeats = 1
```

Then restart Notebook 02's kernel and use the matching model server. The planner
creates fresh experiment records for only the selected conditions belonging to
the active model; historical records remain unchanged. Multiple selected IDs
for one condition are deduplicated. `rerun_repeats`, not `runs_per_config`, sets
the number of additional runs. Unknown IDs are rejected;
`target_experiment_ids` cannot be combined with fresh selective reruns.
Set `rerun_experiment_ids = []` to return to normal matrix scheduling. No audit workflow is required.

Imported databases can use different IDs. Review and refresh the selection after
an import. New synthesis does not guarantee that champion selection will change:
the existing synthesis-error/evaluation-count ranking remains unchanged, and
benchmark outcomes are not used to rank candidates. Additional search motivated
by benchmark feedback must be documented as a follow-up campaign, not silently
substituted into the original thesis results.

Quantization labels identify model artifacts; they do not establish guaranteed
memory requirements, runtime or optimization quality. Report the exact model
artifact and actual experimental settings when comparing results.
