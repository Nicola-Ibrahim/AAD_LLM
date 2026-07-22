# System Architecture Documentation

The system architecture documentation for `AAD_LLM` has been modularized into distinct, focused documents for clarity:

1. [System Architecture & Component Breakdown](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/docs/SYSTEM_ARCHITECTURE.md)
   - High-level C4 container/component diagram.
   - Core domain models, infrastructure layer, and boundary definitions.

2. [Execution Sequence & Resumption Flow](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/docs/EXECUTION_FLOW.md)
   - Step-by-step sequence of dispatching and resuming evolution jobs.
   - Details how checkpoint recovery and warm starts are orchestrated.

3. [LLaMEA Decoupled Architecture](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/docs/LLAMEA_ARCHITECTURE.md)
   - Class and component diagram of the core runtime dependencies (`LLaMEASession`, `Evaluator`, `Logger`, `Repositories`).
   - Deep dive into the fast JSONL decoupled persistence strategy.
