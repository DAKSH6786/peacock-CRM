"""Apply CapabilityRouter decisions onto LLM completion requests."""

from __future__ import annotations

from capability_router.models import RoutingDecision
from capability_router.router import CapabilityRouter
from llm_gateway.ports import LLMCompletionRequest


def apply_routing_decision(
    request: LLMCompletionRequest,
    decision: RoutingDecision,
) -> LLMCompletionRequest:
    """Stamp dynamic provider/model onto a request (no permanent locks)."""
    request.provider = decision.selected.provider_code
    request.model = decision.selected.model_code
    request.task_type = decision.task_type
    request.metadata = {
        **request.metadata,
        "capability_routing": {
            "score": decision.selected.score,
            "source": decision.selected.source,
            "sample_size": decision.selected.sample_size,
            "used_prior_only": decision.used_prior_only,
            "permanent_role_locks": False,
        },
    }
    return request


def route_completion_request(
    router: CapabilityRouter,
    request: LLMCompletionRequest,
    *,
    workspace_id: str,
    task_type: str | None = None,
    allowed_providers: set[str] | None = None,
) -> tuple[LLMCompletionRequest, RoutingDecision]:
    """Dynamically route a gateway request via capability profiles."""
    resolved_task = CapabilityRouter.task_type_for_gateway_role(
        request.role, explicit=task_type or request.task_type
    )
    decision = router.route(
        organisation_id=request.organisation_id,
        workspace_id=workspace_id,
        task_type=resolved_task,
        allowed_providers=allowed_providers,
    )
    request.workspace_id = workspace_id
    return apply_routing_decision(request, decision), decision
