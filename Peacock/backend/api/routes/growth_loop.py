"""Peacock Growth Loop API — the flagship end-to-end workflow.

Public and stateless for now (no DB, no auth — consistent with auth being
disabled for the rest of the application at this stage). Performs a REAL
crawl of the requested URL (and optional competitor URL), so responses take
longer than a typical request and depend on outbound network access.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from api.schemas_growth_loop import GrowthLoopRunRequest
from experiment_engine import evaluate_experiment, list_experiments, log_experiment
from growth_loop import run_growth_loop
from llm_gateway.registry import LLMGateway
from peacock_agents import AGENT_REGISTRY
from peacock_experts import (
    add_comment,
    approve_task,
    assign_task,
    get_task,
    list_tasks,
    mark_ready_to_publish,
    request_changes,
    start_review,
    submit_revision,
)
from peacock_learning import confidence_for_type, list_records
from peacock_publishing import PublishRequest, get_connector, list_connectors

router = APIRouter(prefix="/growth-loop", tags=["growth-loop"])


def _gateway_from_request(request: Request) -> LLMGateway | None:
    return getattr(request.app.state, "llm_gateway", None)


@router.post("/run")
async def run_growth_loop_endpoint(body: GrowthLoopRunRequest, request: Request) -> dict[str, Any]:
    """SEO+AEO+GEO -> AI Visibility -> LLM Intelligence -> Citation/Competitor Gap ->
    Opportunity Engine -> Content Strategy -> Content Creation -> Optimization ->
    AI Agents -> Human Experts -> Publishing -> Measurement -> Experiments -> Learning."""
    try:
        report = await run_growth_loop(
            llm_gateway=_gateway_from_request(request),
            url=body.url,
            competitor_url=body.competitor_url,
            max_pages=body.max_pages,
            engine_codes=body.engine_codes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — surface as a clean error, never a bare 500 stack trace
        raise HTTPException(status_code=502, detail=f"Growth Loop run failed: {exc}") from exc
    return report.to_dict()


@router.get("/agents")
def list_agents() -> dict[str, Any]:
    return {"agents": sorted(AGENT_REGISTRY.keys())}


@router.get("/publishing/connectors")
def publishing_connectors() -> dict[str, Any]:
    return {"connectors": list_connectors()}


class PublishConfirmRequest(BaseModel):
    connector: str = "manual"
    title: str
    body: str
    meta_description: str | None = None
    confirm: bool = False


@router.post("/publishing/preview")
async def publishing_preview(body: PublishConfirmRequest) -> dict[str, Any]:
    try:
        connector = get_connector(body.connector)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    result = await connector.publish(
        PublishRequest(title=body.title, body=body.body, meta_description=body.meta_description),
        confirm=body.confirm,
    )
    return result.to_dict()


@router.get("/experts/tasks")
def list_expert_tasks(status: str | None = None, assignee: str | None = None) -> dict[str, Any]:
    return {"tasks": [t.to_dict() for t in list_tasks(status=status, assignee=assignee)]}


@router.get("/experts/tasks/{task_id}")
def get_expert_task(task_id: str) -> dict[str, Any]:
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Unknown expert task")
    return task.to_dict()


class AssignRequest(BaseModel):
    assignee: str
    assignee_role: str


@router.post("/experts/tasks/{task_id}/assign")
def assign_expert_task(task_id: str, body: AssignRequest) -> dict[str, Any]:
    try:
        return assign_task(task_id, assignee=body.assignee, assignee_role=body.assignee_role).to_dict()
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class CommentRequest(BaseModel):
    author: str
    body: str


@router.post("/experts/tasks/{task_id}/comment")
def comment_expert_task(task_id: str, body: CommentRequest) -> dict[str, Any]:
    try:
        return add_comment(task_id, author=body.author, body=body.body).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/experts/tasks/{task_id}/start-review")
def review_expert_task(task_id: str) -> dict[str, Any]:
    try:
        return start_review(task_id).to_dict()
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class ChangesRequestBody(BaseModel):
    reviewer: str
    note: str


@router.post("/experts/tasks/{task_id}/request-changes")
def request_expert_changes(task_id: str, body: ChangesRequestBody) -> dict[str, Any]:
    try:
        return request_changes(task_id, reviewer=body.reviewer, note=body.note).to_dict()
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class RevisionBody(BaseModel):
    author: str
    content: str
    note: str | None = None


@router.post("/experts/tasks/{task_id}/submit-revision")
def submit_expert_revision(task_id: str, body: RevisionBody) -> dict[str, Any]:
    try:
        return submit_revision(task_id, author=body.author, content=body.content, note=body.note).to_dict()
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class ApprovalBody(BaseModel):
    approver: str


@router.post("/experts/tasks/{task_id}/approve")
def approve_expert_task(task_id: str, body: ApprovalBody) -> dict[str, Any]:
    try:
        return approve_task(task_id, approver=body.approver).to_dict()
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/experts/tasks/{task_id}/ready-to-publish")
def ready_to_publish_task(task_id: str) -> dict[str, Any]:
    try:
        return mark_ready_to_publish(task_id).to_dict()
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class ExperimentRequest(BaseModel):
    hypothesis: str
    page_url: str
    change_description: str
    change_category: str = "other"


@router.post("/experiments")
def create_experiment(body: ExperimentRequest) -> dict[str, Any]:
    return log_experiment(
        hypothesis=body.hypothesis,
        page_url=body.page_url,
        change_description=body.change_description,
        change_category=body.change_category,
    ).to_dict()


@router.get("/experiments")
def get_experiments(page_url: str | None = None) -> dict[str, Any]:
    return {"experiments": [e.to_dict() for e in list_experiments(page_url)]}


@router.post("/experiments/{experiment_id}/evaluate")
def evaluate_experiment_endpoint(experiment_id: str) -> dict[str, Any]:
    try:
        return evaluate_experiment(experiment_id).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/learning/records")
def get_learning_records(page_url: str | None = None, recommendation_type: str | None = None) -> dict[str, Any]:
    return {"records": [r.to_dict() for r in list_records(page_url=page_url, recommendation_type=recommendation_type)]}


@router.get("/learning/confidence/{recommendation_type}")
def get_confidence(recommendation_type: str) -> dict[str, Any]:
    return confidence_for_type(recommendation_type).to_dict()
