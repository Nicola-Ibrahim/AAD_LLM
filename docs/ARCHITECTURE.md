# System Architecture & Documentation Index

The technical documentation for `AAD_LLM` is structured into focused directories:

## 🏛️ Architecture Documentation (`docs/architecture/`)
1. [System Architecture & Component Breakdown](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/docs/architecture/system_architecture.md)
   - High-level C4 container/component diagram.
   - Core domain models, infrastructure layer, and boundary definitions.
2. [Execution Sequence & Resumption Flow](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/docs/architecture/execution_flow.md)
   - Step-by-step sequence of orchestrating and resuming evolution tasks.
   - Details how checkpoint recovery and warm starts are orchestrated.
3. [LLaMEA Decoupled Architecture](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/docs/architecture/llamea_architecture.md)
   - Class and component diagram of runtime dependencies (`LLaMEASession`, `Evaluator`, `Logger`, `Repositories`).
   - Deep dive into the fast JSONL decoupled persistence strategy.
4. [Evolutionary Synthesis & Evaluator Methodology](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/docs/evaluator_methodology.md)
   - Comprehensive breakdown of the evolutionary search loop, `Evaluator` architecture, and mathematical scoring formulations.
   - Mathematical definitions of ground-truth optimality gaps, Euclidean decision space distances, and noise injection models.

## ⚙️ Configuration Documentation (`docs/configuration/`)
1. [Model & LLM Configuration Guide](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/docs/configuration/model_configuration.md)
   - Guide for configuring local GGUF models via llama.cpp/Ollama and external API providers.
   - Prompt strategy setup and hyperparameter configuration (`configs/llms.toml`).

## 📋 Roadmaps & Plans (`docs/plans/`)
- Contains detailed design documents, RFCs, and integration plans (e.g. `IOHAnalyzer.md`).
