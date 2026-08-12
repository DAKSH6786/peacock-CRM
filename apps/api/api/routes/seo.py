"""Peacock SEO Engine API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_seo import SeoAuditRequest, SeoAuditResponse
from crawler.sqlalchemy_store import SqlAlchemyCrawlStore
from observability.audit import AuditEvent, AuditLogger
from seo_engine import PeacockSeoEngine
from seo_engine.persistence import persist_audit_report

router = APIRouter(prefix="/seo", tags=["peacock-seo-engine"])
audit_logger = AuditLogger()

# Process-local report cache for GET after POST (also persisted when requested)
_REPORTS: dict[str, dict] = {}


def _to_response(payload: dict) -> SeoAuditResponse:
    return SeoAuditResponse(**payload)


@router.post("/audits", response_model=SeoAuditResponse, status_code=201)
async def create_seo_audit(
    body: SeoAuditRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> SeoAuditResponse:
    store = SqlAlchemyCrawlStore(db)
    crawl = store.get_crawl(body.crawl_id)
    if crawl is None or crawl.organisation_id != ctx.organisation.id:
        raise HTTPException(status_code=404, detail="Crawl not found")

    engine = PeacockSeoEngine()
    report = await engine.audit_crawl(crawl, fetch_connectors=body.fetch_connectors)
    if body.persist:
        if not report.website_id:
            raise HTTPException(status_code=400, detail="Crawl has no website_id; cannot persist audit")
        persist_audit_report(db, report)

    payload = report.to_dict()
    _REPORTS[report.id] = payload

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="seo.audit.create",
            resource_type="audit",
            resource_id=report.id,
            workspace_id=crawl.workspace_id,
            metadata={
                "crawl_id": crawl.id,
                "peacock_seo_score": report.peacock_seo_score.score,
            },
        )
    )
    return _to_response(payload)


@router.get("/audits/{audit_id}", response_model=SeoAuditResponse)
def get_seo_audit(
    audit_id: str,
    ctx: AuthContext = Depends(get_auth_context),
) -> SeoAuditResponse:
    payload = _REPORTS.get(audit_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Audit not found in session cache")
    if payload.get("organisation_id") != ctx.organisation.id:
        raise HTTPException(status_code=404, detail="Audit not found")
    return _to_response(payload)


@router.get("/audits/{audit_id}/overview", response_model=SeoAuditResponse)
def get_seo_audit_overview(
    audit_id: str,
    ctx: AuthContext = Depends(get_auth_context),
) -> SeoAuditResponse:
    return get_seo_audit(audit_id, ctx)
