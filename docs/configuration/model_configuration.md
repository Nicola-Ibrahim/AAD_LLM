# Model configuration

[Documentation map](../README.md) · [Project README](../../README.md)

Provider connections, server settings, model presets and experimental settings
have different owners; model selection is not entirely configuration-free.

## Provider connections

[LLMClient](../../src/evolution/infra/llm/client.py) supports `local`, `lmstudio`,
`upb` and `gemini`. The notebook supplies the provider and optional client arguments.
Environment variables provide defaults:

| Provider | URL | Model | API key |
| --- | --- | --- | --- |
| Local | `LOCAL_LLM_BASE_URL` | `LOCAL_LLM_MODEL` | `LOCAL_LLM_API_KEY` |
| LM Studio | `LLM_STUDIO_BASE_URL` | `LLM_STUDIO_MODEL` | `LLM_STUDIO_API_KEY` |
| Gemini | Provider-managed | `GEMINI_MODEL` | `GOOGLE_API_KEY` |
| University Paderborn | `UPB_API_BASE` | `UPB_MODEL` | `UPB_API_KEY` |

Local and LM Studio default to `http://localhost:1234/v1`.
An explicit `model=` argument takes precedence over the model environment variable.
With connection validation enabled and no configured model, the client discovers
the first model returned by the endpoint's `/models` response. With validation
disabled, a model must be supplied. `SKIP_LLM_VALIDATION=True` disables the
connection probe; it is not a substitute for configuring the model.
Keep API keys in local environment configuration, not committed documents.

### University gateway through LLaMEA

Set these values in the ignored `.env` file; never put a real key in a notebook:

```dotenv
LLM_PROVIDER=upb
UPB_API_BASE=https://ai-gateway.uni-paderborn.de/v1/
UPB_API_KEY=replace-with-your-private-key
UPB_MODEL=gwdg.qwen3-30b-a3b-instruct-2507
```

Notebook 02 resolves `SynthesisCampaignCoordinator`; `EvolutionProvider` creates
the LLM connection from `LLM_PROVIDER` and owns its cleanup. The notebook does not
import, construct or call `LLMClient`. The existing LLaMEA `OpenAI_LLM` adapter
issues synthesis requests, not a separate example script.
Connection checks and model discovery send Bearer authentication. Unlike a local
single-model server, the gateway requires an explicit model ID: it never silently
selects the first catalogue entry. List your accessible IDs without generating text:

```python
print("\n".join(llm.list_models()))
```

The [gateway catalogue](upb_models.md) records one account's discovery snapshot;
refresh via `list_models()` because permissions and availability can change.
Use named models rather than `latest` aliases or routers for reproducible studies.
For now prefer the documented Qwen3 instruct model; other models, particularly
reasoning models, need a smoke test for LLaMEA's `temperature` setting and plain-text
code output before a campaign. Listing is not proof of generation entitlement.
The gateway catalogue supplies no prices, so no cheapest-model claim follows from it.

CPU-worker capacity is selected automatically from process CPU availability,
affinity and `SLURM_CPUS_PER_TASK` when available. It is not a TOML setting or a
public campaign argument. This works for local and hosted models; worker
concurrency does not set the HTTP request rate.

The gateway adapter automatically selects request pacing from the model's provider:

| Provider selection | Request starts per minute | Worker scheduling |
| --- | ---: | --- |
| `local` / `lmstudio` | No added throttling | Automatic CPU parallel pool |
| `upb`, model ID beginning `gwdg.` | 8 | Same parallel pool |
| `upb`, model ID beginning `kiconnect.` | 80 | Same parallel pool |
| `upb`, model ID beginning `openai.` | 80 | Same parallel pool |

The UPB defaults leave 20% headroom below the published 10/100/100 RPM limits.
The [university budget guidance](https://hilfe.uni-paderborn.de/Budgets_im_AI-Chat_und_AI-Gateway)
also confirms that GWDG and KIConnect have no consumption charges; OpenAI use draws
from the person's $20 monthly allowance. API and Chat share resources. Overnight
execution can reduce contention but does not waive quotas.

Pacing is shared by worker processes and other project notebooks on the **same host
and OS account**, grouped by gateway URL and upstream provider, not by model or API
key. A small SQLite file in the user's private system-temporary directory stores
only request timestamps and hashed provider scopes. It is runtime coordination state,
not another synthesis database: no migrations, credentials, generated code, or stored
experimental results are involved. It is intentionally outside `data/` and `results/`.
No Redis service or additional process manager is needed.

Every SDK HTTP attempt, including validation and listing, passes through this gate.
Gateway retries have one owner rather than nested SDK/LLaMEA/wrapper network retries;
temporary failures use bounded attempts and shared `Retry-After` cooldowns. Permanent
authentication/request errors and recognized exhausted-budget error codes propagate
without retrying the same API operation. Already queued independent sessions can still
encounter the same account error; this is not a campaign-wide budget accounting system.
Local-client retry behavior and LLaMEA's prompts/code extraction remain unchanged.

If your actual key has a lower or specially approved higher provider quota, set
`UPB_REQUESTS_PER_MINUTE` once in `.env`. For an unlisted upstream prefix such as
`pc2.`, `hs-de.` or a router, this value is required rather than guessing a quota.
For diagnostics/tests, `UPB_RATE_LIMIT_STATE` can override the runtime-state file.
Use consistent caps across simultaneous jobs. Separate machines do not share this
gate; allocate the account quota between them. Browser Chat requests are not tracked
by our code, so headroom cannot guarantee avoidance of all server-side rate limits.

This controls **RPM**, not proactive TPM or monthly spending. Model-specific token
limits, other account activity and university-wide load can still produce 429 errors.
Check the gateway's Max TPM/Max RPM fields and remaining budget before a campaign;
do not shorten scientific prompts or change objective-call budgets to work around quotas.
No generation call is required to validate connectivity.
The hosted model is recorded separately from historical GGUF model IDs.
Restart the notebook kernel after changing providers or model environment settings.

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

### Explicit study parameters

Scientific study settings are passed directly to application methods. There are
no synthesis, benchmark or baseline TOML loaders. Notebook 02 defines
`synthesis_parameters`; notebook 03 defines `benchmark_parameters` visibly in
their setup cells. A future HTTP adapter can pass the same fields without a
configuration-file dependency.

| Method | Explicit study inputs |
| --- | --- |
| `run_campaign(...)`, `audit_matrix(...)` | `problem_targets`, `noise_conditions`, `synthesis_modes`, `iterations`, `budget`, `timeout_seconds`, `runs_per_config`, `auto_resume`, `skip_completed`, `retry_failed_synthesis` |
| `run_benchmarks(...)`, `audit_workload(...)`, `summarize_results(...)` | `trials_per_condition`, `random_seed`, `first_instance_id`, `budget`, `trial_timeout_seconds`, `observation_trace_points`, `force_rerun`, `classical_baselines`, `noise_robustness_enabled`, `cross_function_enabled`, `cross_function_problem_ids` |
| Summary thresholds | `primary_target`, `secondary_target` |
| Analysis operations | Setup supplies validated `BenchmarkConfig` and `ReliabilityConfig`; the four use cases accept condition filters through `execute(...)` |

Parameters are keyword-only. Pydantic validates values before planning, discovery,
dispatch or writes; ordinary model fields and validators describe structured
problem/noise/mode entries. Model identity comes from the connected LLM, and
CPU-worker capacity is selected automatically. Credentials, database paths and
infrastructure collaborators are server-managed, not experiment body fields.

Context-owned Dishka providers live in `evolution/infra/di.py` and
`benchmark/infra/di.py`. The application coordinator receives concrete workload and trial-runner objects.
Notebook setup resolves ready application services and owns their workflow scope.
Ordinary cells call those services directly, without forwarding module methods.
A future FastAPI host can reuse the providers and native Dishka request injection;
HTTP handlers do not construct services. Dishka supplies constructor dependencies;
execution settings remain explicit method arguments. Analysis settings are typed
setup data, fixed for the scope rather than mutated between calls.

For example, a small explicit synthesis request is:

```python
# campaign is resolved once in notebook setup.
results = campaign.run_campaign(
    problem_targets=[{"id": 15, "dimensions": [10]}],
    noise_conditions=[{"std": 0.1, "noise_model": "heteroscedastic"}],
    synthesis_modes=[{"mode": "explicit", "strategies": ["baseline"]}],
    iterations=10,
    budget=100_000,
    timeout_seconds=30.0,
    runs_per_config=1,
    auto_resume=True,
    skip_completed=True,
    retry_failed_synthesis=True,
)

```

Notebooks may collect these visible arguments in a dictionary and unpack it into
the same method. Native, baseline, noise-robustness and cross-function benchmark
work use `run_benchmarks(solver_type=..., **benchmark_parameters)`.
`audit_workload(...)` and `summarize_results(...)` are read-only; neither launches
trials. The optional study gates, missing-data policy and dynamic model discovery
are unchanged. No HTTP server, queue or frontend is introduced.

`configs/llms.toml` remains provider/model-registry metadata. It is unrelated to
the scientific execution parameters and does not determine completed models.

### Selective synthesis reruns

Keep study parameters visible in the notebook; pass selections to each campaign call:

```python
# Automatic recovery only, for the active LLM:
campaign_usecase.run_campaign(**synthesis_parameters, recover=True)

# Recovery plus manually selected conditions (review IDs for the current DB):
campaign_usecase.run_campaign(
    **synthesis_parameters,
    recover=True,
    rerun_experiment_ids=[2091, 2737, 2147],
)

# Resume specific running sessions, without scheduling other work:
campaign_usecase.run_campaign(**synthesis_parameters, resume_experiment_ids=[123])

# Fill the full configured matrix to its replicate target:
campaign_usecase.run_campaign(**synthesis_parameters)
```

Use the matching model server. These options are invocation-scoped: changing IDs
does not require editing configuration files or restarting the kernel. After updating Python
code, restart Notebook 02's kernel. The planner
combines explicit replacement requests with configured-matrix recovery for the active model:
interrupted sessions are resumed when `auto_resume` is enabled, and unresolved
synthesis failures receive one fresh attempt when `retry_failed_synthesis` is
enabled, but only when the condition has no completed valid champion. Any completed
valid champion satisfies automatic recovery, even if individual candidate iterations,
other sessions, or leftover queued records failed. Manual rerun IDs restart those
exact records from generation one: old iterations, diagnostics, champion fields,
generated code and checkpoints are removed. No new experiment rows are inserted.
Duplicate IDs run once; different explicitly selected IDs remain separate records.
For an uncovered condition, automatic recovery resumes one pending record or
replaces one existing failed record. This path does not expand unrelated conditions
into extra replicates. Unknown IDs are rejected before work is dispatched;
`resume_experiment_ids` cannot be combined with recovery or replacement, and only
running records belonging to the active LLM are resumed. No audit workflow is required.
Each call rediscovers database state. Automatic recovery needs no manual IDs.
Logs show only `Exp ID`, which remains the requested ID during replacement.
Stop any campaign executing the same records before replacing them. Replacement
is destructive and does not retain the old result history; merely auditing or
planning does not reset records. Reset occurs when execution begins.
Omit manual IDs after successful repairs: explicitly passing them again requests
another replacement. There is no `rerun_repeats` option for in-place replacement. The
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
an import. After replacement, reload champion selection and rerun affected benchmark
evaluations; prior benchmark outputs describe the old code and are not regenerated
by synthesis. The existing champion-ranking rules remain unchanged, and benchmark
outcomes are not used to rank candidates. Additional search motivated
by benchmark feedback must be documented as a follow-up campaign, not silently
substituted into the original thesis results.

Quantization labels identify model artifacts; they do not establish guaranteed
memory requirements, runtime or optimization quality. Report the exact model
artifact and actual experimental settings when comparing results.
