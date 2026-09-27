# Documentation map

[Back to project README](../README.md)

Start with the project README for setup, configuration and the notebook workflow.
Use these guides for deeper explanations; each topic has one primary home.

## Choose a guide

| Question | Guide |
| --- | --- |
| How is the modular monolith organized, and who owns each responsibility? | [System architecture](architecture/system_architecture.md) |
| How are synthesis sessions dispatched, persisted and resumed? | [Execution and recovery](architecture/execution_flow.md) |
| What is scored, how are budgets/timeouts handled, and how do native/noise/transfer studies differ? | [Evaluation protocol](evaluation_protocol.md) |
| How do I configure a provider, serve a model and discover its identity? | [Model configuration](configuration/model_configuration.md) |
| Which analysis notebook should I run, and where do its figures go? | [Analysis workflow guide](../notebooks/analysis/README.md) |

## Architecture views

- [Compact workflow overview](../README.md#level-0--workflow-overview): quick orientation, rendered with Mermaid.
- [Detailed system diagram](../README.md#level-1--detailed-system-view): components, relationships and code links, rendered with Mermaid.
- [Level 0 Mermaid source](architecture/system_overview.mmd): editable workflow overview.
- [Level 1 Mermaid source](architecture/system_diagram.mmd): editable detailed system diagram.
- [Synthesis collaboration](architecture/system_architecture.md#synthesis-collaboration): editable Mermaid showing LLaMEA, application workflows, execution and scoring.
- [Candidate evaluation](evaluation_protocol.md#synthesis-candidate-scoring): editable Mermaid showing validation, clean scoring and failure classification.

The overview and detailed system diagrams appear directly in the project README;
the focused diagrams appear in their architecture/protocol guides. They describe workflows and
supporting capabilities, not strict C4 levels or Python import dependencies.

## Sources of truth

Implementation guides describe current behavior. [Configuration files](../configs/)
define defaults for new runs; completed database records and result provenance
describe what historical experiments actually used. Do not treat current defaults
as proof of historical settings or numerical findings.

Scientific calculations belong to domain/shared code. Notebook-owned helpers handle
figures and exports. Documentation edits do not rerun campaigns or regenerate results.
