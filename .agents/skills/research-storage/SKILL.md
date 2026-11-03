---
name: research-storage
description: Change or inspect AAD_LLM SQLite repositories, artifact storage, checkpoints, provenance or archives while preserving experiments and recovery.
---

# Work on research storage

## 1. Identify the storage operation

Inputs: the storage question/change, relevant repository/adapter and callers, and
applicable schema/provenance formats or explicitly requested source/destination.
Use [research-change](../research-change/SKILL.md) for substantial-task phases,
records and handoff. Do not infer permission for data operations from a code task.

Read the affected repository/adapter, its callers and applicable schema/provenance
formats. Consult [execution and recovery](../../../docs/architecture/execution_flow.md)
and [benchmark protocol](../../../docs/benchmark_protocol.md) when resumption is involved.
Inspect metadata without exposing credentials or private payloads.

Identify the owner and operation first: evolution owns synthesis-table semantics
and writes; benchmark infrastructure has the documented read-only candidate view.
Distinguish synthesis DB records, generated code/checkpoints, benchmark terminal
outcomes, IOH traces, calculated analysis snapshots and exported figures.

## 2. Follow only the applicable branch

**Read-only inspection:** use read-only database access and inspect relevant metadata
and formats. Do not initialize writer-enabling adapters merely to inspect a study.
Return findings and recovery/provenance limits in chat or the permitted task record;
stop without repairing, archiving or deleting data.

**Authorized code change:** use disposable SQLite and artifact fixtures. Preserve WAL/session
behavior, transaction boundaries, identifiers, code hashes, schema/error definitions,
paths and formats unless an explicit change is authorized. Check failure causes and
partial-write behavior; do not hide corruption as missing data. Keep audit read-only.
A missing synthesis checkpoint cannot be recreated from terminal errors; never
silently replace an experiment or delete partial work to make resume succeed.

**Explicitly authorized archive, restore, cleanup or migration:** enumerate
sources and destinations first. Stop relevant writers for a consistent snapshot;
use SQLite's supported backup mechanism for an active/WAL database rather than
copying only its main file. Verify integrity, artifact checksums and associated
configuration/code provenance. Keep the verified archive until replacement is
confirmed; prevent new protocol results merging with historical storage.

## 3. Return evidence and stop

For code changes, return the adapter changes and checks required by the storage
contract. Use [research-verification](../research-verification/SKILL.md) for safe
check execution and isolation; do not duplicate its harness here.
For authorized data operations, report source/destination, artifacts preserved,
actual integrity/checksum results and recovery limits. Stop when the requested
operation is complete; an archive does not authorize a subsequent reset or deletion.
If consistency or preservation cannot be verified, report the gap and stop before
destructive follow-up. Research-change owns task-record updates when applicable.

This procedure grants no permission to mutate real study data. Do not launch
migrations, cleanup or restores against a study database just to test an adapter.
