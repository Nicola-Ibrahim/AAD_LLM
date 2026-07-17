import json
from pathlib import Path
from storage.manager import ExperimentManager


def recover_orphaned_checkpoints(checkpoint_dir: Path, storage_manager: ExperimentManager) -> int:
    """
    Scans the checkpoint directory for orphaned .ckpt.json files and recovers them.

    If recovery is successful, the checkpoint file is deleted.

    Returns
    -------
    int
        The number of successfully recovered experiment runs.
    """
    recovered_count = 0
    checkpoint_dir = Path(checkpoint_dir)
    if not checkpoint_dir.exists():
        return 0

    for ckpt_path in sorted(checkpoint_dir.glob("*.ckpt.json")):
        try:
            with ckpt_path.open("r") as f:
                envelope = json.load(f)

            experiment_meta = envelope.get("experiment")
            iterations = envelope.get("iterations")

            if not experiment_meta or not iterations:
                # Malformed or empty checkpoint file, delete it
                ckpt_path.unlink()
                continue

            storage_manager.save_from_checkpoint(
                experiment_meta=experiment_meta,
                iterations_data=iterations,
            )

            ckpt_path.unlink()
            recovered_count += 1
            print(
                f"[recovery] Recovered crashed run {experiment_meta.get('run_id')} for "
                f"BBOB-{experiment_meta.get('problem_id')} ({experiment_meta.get('mode')})"
            )
        except Exception as e:
            print(f"[recovery] Failed to recover {ckpt_path.name}: {e}")

    return recovered_count
