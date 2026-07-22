from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunContext:
    """Pre-execution context returned by ExperimentRepository.create_experiment().

    Contains all paths and IDs the session needs before firing the evolution loop.
    All directories are guaranteed to exist when this object is returned.
    """

    run_id: int
    archive_dir: Path
    checkpoint_dir: Path
