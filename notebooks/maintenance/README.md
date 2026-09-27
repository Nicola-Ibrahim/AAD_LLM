# Synthesis database maintenance

The notebook wires the application `SynthesisDuplicateMaintenance` use case to
`SQLiteDuplicateStorage`. Retention policy, preview validation and authorization
belong to the application; database access, backups and artifact quarantine belong
to infrastructure. The adapter revalidates the plan under its writer lock.

Open [cleanup_synthesis_duplicates.ipynb](cleanup_synthesis_duplicates.ipynb)
to inspect repeated conditions and review exact IDs before deleting anything.

The default is preview-only and preserves valid completed runs and interrupted
progress. Optional one-per-condition mode keeps the best completed result using
the existing error/evaluation-count ranking. Different model, function, dimension,
instance, mode, noise, strategy, budget or iteration protocols are separate groups.

Application requires all jobs stopped and an exact confirmation. A SQLite backup
and plan are written under `data/maintenance_backups/` before deletion. Optional
artifact cleanup quarantines selected code/checkpoint directories in that backup;
it never deletes benchmark traces or figures. A changed database requires a new
preview. No schema migration or synthesis/evaluation campaign is launched.

After cleanup, refresh synthesis audit and champion selection/readiness. Existing
benchmark exports referencing removed IDs may require regeneration or reevaluation.
Recovery instructions are included in the notebook; do not restore a live database.
