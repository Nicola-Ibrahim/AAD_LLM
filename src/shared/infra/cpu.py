"""Resolve local execution capacity without exposing worker tuning in study APIs."""

import os


def available_cpu_count() -> int:
    """Respect process affinity and scheduler allocations when available."""
    process_count = getattr(os, "process_cpu_count", os.cpu_count)
    limits = [process_count() or 1]
    if hasattr(os, "sched_getaffinity"):
        limits.append(len(os.sched_getaffinity(0)))
    allocation = os.getenv("SLURM_CPUS_PER_TASK", "")
    if allocation.isdecimal() and int(allocation) > 0:
        limits.append(int(allocation))
    return max(1, min(limits))
