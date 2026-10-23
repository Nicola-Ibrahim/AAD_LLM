# University gateway model catalogue

[Model configuration](model_configuration.md) · [Documentation map](../README.md)

Account-specific discovery snapshot retrieved on **23 October 2026** using authenticated
`GET https://ai-gateway.uni-paderborn.de/v1/models` through our `LLMClient("upb")`.
The gateway advertised **82 model IDs**. No generation requests were made.
No API keys or user identifiers are included here.

This is the gateway's advertised catalogue, not verification of each underlying model,
Chat Completions compatibility, price, allowance or generation entitlement. The response
provided no pricing. Permissions and aliases can change; refresh with `llm.list_models()`.
Embedding models cannot generate optimizer programs. Avoid `latest` aliases and routers
for controlled comparisons. Keep new hosted-model experiments separate from the archived
GGUF results; changing the provider does not regenerate or overwrite historical results.

## Initial selection

`gwdg.qwen3-30b-a3b-instruct-2507` is configured in the ignored `.env` file because it is
explicitly demonstrated in the [university instructions](https://hilfe.uni-paderborn.de/AI-Gateway)
and appeared in this account's catalogue. It is **not a verified cheapest-model selection**.

Other candidates for a small comparison are `gwdg.meta-llama-3.1-8b-instruct` and
`gwdg.qwen3-coder-next`. Check your institution's billing/quotas and perform an approved
single-generation smoke test before committing to a complete campaign. Catalogue entries
are not evidence that any model will outperform the historical champions.

GWDG describes its hosted models as free in its own [Chat AI service](https://docs.hpc.gwdg.de/services/ai-services/chat-ai/index.html),
but that does not establish the UPB gateway's account-specific pricing or quotas.
The [linked university terms](https://www.uni-paderborn.de/fileadmin/imt/datenschutz/KI-Chat/KI-Chat_Betriebsregeln.pdf)
contain restrictions on automated output extraction; obtain clarification for automated
LLaMEA research campaigns. `max_workers = 1` limits simultaneous sessions only, not overall
request/token consumption. Current LLaMEA sends a temperature parameter; some reasoning
models may require a different request adapter and are not automatically interchangeable.

## gwdg (20)

```text
gwdg.meta-llama-3.1-8b-instruct
gwdg.qwen3-30b-a3b-instruct-2507
gwdg.qwen3-omni-30b-a3b-instruct
gwdg.qwen3.5-397b-a17b
gwdg.qwen3.5-397b-a17b-no-think
gwdg.qwen3.6-35b-a3b
gwdg.qwen3.6-35b-a3b-no-think
gwdg.gemma-4-31b-it
gwdg.qwen3-coder-next
gwdg.deepseek-v4-flash-0731
gwdg.qwen3.8-27b
gwdg.qwen3.8-27b-no-think
gwdg.glm-5.3-flash
gwdg.e5-mistral-7b-instruct
gwdg.multilingual-e5-large-instruct
gwdg.qwen3-embedding-4b
gwdg.latest-taskmodel
gwdg.latest-basemodel
gwdg.latest-basemodel-no-thinking
gwdg.qwen-complexity-router
```

## pc2 (5)

```text
pc2.latest-basemodel
pc2.meta-llama/Llama-3.1-8B-Instruct
pc2.Qwen/Qwen3-32B
pc2.Qwen/Qwen3-Next-80B-A3B-Thinking
pc2.Qwen/Qwen3-Next-80B-A3B-Instruct
```

## kiconnect (5)

```text
kiconnect.openai-gpt-oss-120b
kiconnect.mistralai-mistral-small-4-119b-2603
kiconnect.qwen3.8-27b
kiconnect.e5-mistral-7b-instruct
kiconnect.qwen3-embedding-8b
```

## hs-de (9)

```text
hs-de.latest-taskmodel
hs-de.latest-basemodel
hs-de.latest-basemodel-no-thinking
hs-de.complexity-router
hs-de.moeve-router
hs-de.openai-gpt-oss-120b
hs-de.qwen3.8-27b
hs-de.qwen3.8-27b-no-think
hs-de.e5-mistral-7b-instruct
```

## openai (42)

```text
openai.latest-basemodel
openai.latest-taskmodel
openai.o3
openai.o3-mini
openai.gpt-4o
openai.gpt-4o-mini
openai.gpt-4.1
openai.gpt-4.1-mini
openai.o4-mini
openai.gpt-5
openai.gpt-5-mini
openai.gpt-5-nano
openai.gpt-5.1
openai.gpt-5.2
openai.gpt-5.3-codex
openai.gpt-5.4
openai.gpt-5.4-mini
openai.gpt-5.4-nano
openai.gpt-5.5
openai.gpt-5.6-sol
openai.gpt-5.6-terra
openai.gpt-5.6-luna
openai.gpt-6-astra
openai.gpt-6-luna
openai.gpt-6-sol
openai.gpt-6.1-sol
openai.chat-latest
openai.gpt-5.5-flex
openai.gpt-5.6-luna-medium
openai.gpt-5.6-luna-high
openai.gpt-5.6-luna-max
openai.gpt-5.6-sol-xhigh
openai.gpt-5.6-sol-max
openai.gpt-6-luna-medium
openai.gpt-6-luna-high
openai.gpt-6-luna-max
openai.gpt-6-sol-xhigh
openai.gpt-6-sol-max
openai.gpt-6.1-sol-xhigh
openai.gpt-6.1-sol-max
openai.complexity-router
openai.complexity-router-gpt-5.6
```

## mixed (1)

```text
mixed.complexity-router
```
