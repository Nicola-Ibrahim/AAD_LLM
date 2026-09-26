"""Compose a dashboard across contexts using plain synthesis-condition metadata."""

from benchmarking.application.evaluation.audit import EvaluationAuditService, SynthesisConditionSpec
from bootstrap.evaluation import build_evaluation_workflow
from evolution.infra.storage.synthesis_config.repository import SynthesisConfigRepository


def build_audit_service() -> EvaluationAuditService:
    synthesis = SynthesisConfigRepository().load_config()
    specs = tuple(
        dict.fromkeys(
            SynthesisConditionSpec(c.problem_id, c.dim, c.noise_std, c.mode.value, c.strategy.value)
            for c in synthesis.matrix_conditions
        )
    )
    workflow = build_evaluation_workflow(
        planned_target_conditions=tuple(sorted({(s.dim, s.noise_std, s.problem_id) for s in specs}))
    )
    return EvaluationAuditService(workflow.service.workload, workflow.sqlite_repo, specs)
