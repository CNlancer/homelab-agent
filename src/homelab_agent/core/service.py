from homelab_agent.core.audit import AuditLogger
from homelab_agent.core.router import ActionRouter
from homelab_agent.models.result import ExecutionResult
from homelab_agent.models.task import TaskSpec


class ExecutionService:
    def __init__(self, router: ActionRouter, audit_logger: AuditLogger) -> None:
        self._router = router
        self._audit_logger = audit_logger

    def execute(self, task: TaskSpec) -> ExecutionResult:
        registered_action = self._router.resolve(task)
        output = registered_action.handler(task)
        result = ExecutionResult(
            target_type=task.target_type,
            target_name=task.target_name,
            action=task.action,
            risk_level=task.risk_level,
            confirmation_required=task.confirmation_required,
            success=True,
            summary="{0}.{1} completed successfully".format(task.target_type, task.action),
            output=output,
        )
        self._audit_logger.record(result)
        return result
