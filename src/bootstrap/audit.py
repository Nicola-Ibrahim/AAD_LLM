"""Compose a dashboard across contexts using plain synthesis-condition metadata."""

from collections.abc import Iterator
from contextlib import contextmanager

from benchmarking.application.benchmark.audit import BenchmarkAuditService, SynthesisConditionSpec
from bootstrap.benchmark import build_benchmark_workflow


@contextmanager
def build_audit_service(
    *,
    planned_conditions: tuple[SynthesisConditionSpec, ...] = (),
) -> Iterator[BenchmarkAuditService]:
    specs = tuple(dict.fromkeys(planned_conditions))
    with build_benchmark_workflow(
        planned_target_conditions=tuple(sorted({(s.dim, s.noise_std, s.problem_id) for s in specs}))
    ) as workflow:
        yield BenchmarkAuditService(workflow.service.workload, workflow.sqlite_repo, specs)
