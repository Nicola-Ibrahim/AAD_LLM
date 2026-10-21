"""Compose a dashboard across contexts using plain synthesis-condition metadata."""

from benchmarking.application.benchmark.audit import BenchmarkAuditService, SynthesisConditionSpec
from bootstrap.benchmark import build_benchmark_workflow
from evolution.infra.storage.synthesis_config.repository import SynthesisConfigRepository


def build_audit_service() -> BenchmarkAuditService:
    synthesis = SynthesisConfigRepository().load_config()
    specs = tuple(
        dict.fromkeys(
            SynthesisConditionSpec(c.problem_id, c.dim, c.noise_std, c.mode.value, c.strategy.value)
            for c in synthesis.matrix_conditions
        )
    )
    workflow = build_benchmark_workflow(
        planned_target_conditions=tuple(sorted({(s.dim, s.noise_std, s.problem_id) for s in specs}))
    )
    return BenchmarkAuditService(workflow.service.workload, workflow.sqlite_repo, specs)
