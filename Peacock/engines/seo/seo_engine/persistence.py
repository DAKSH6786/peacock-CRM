"""Persist SeoAuditReport into Audit* / SEOScore tables."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from db_models import (
    Audit,
    AuditIssue,
    AuditMetric,
    AuditRecommendation,
    AuditSection,
    SEOScore,
)
from db_models.base import new_uuid
from seo_engine.models import SeoAuditReport


def persist_audit_report(session: Session, report: SeoAuditReport) -> Audit:
    if not report.website_id:
        raise ValueError("website_id is required to persist an SEO audit")

    now = datetime.now(UTC)
    audit = Audit(
        id=report.id,
        organisation_id=report.organisation_id,
        workspace_id=report.workspace_id,
        website_id=report.website_id,
        crawl_id=report.crawl_id,
        audit_type="seo",
        title=report.title,
        summary=report.summary,
        overall_score=report.peacock_seo_score.score,
        started_at=now,
        completed_at=now,
        status="completed",
    )
    session.add(audit)
    session.flush()

    # Overall peacock score section
    all_scores = {
        "peacock_seo_score": report.peacock_seo_score,
        **report.scores,
    }
    for code, score in all_scores.items():
        section = AuditSection(
            id=new_uuid(),
            organisation_id=report.organisation_id,
            workspace_id=report.workspace_id,
            audit_id=audit.id,
            code=code,
            title=score.label,
            score=score.score,
            summary=(
                f"confidence={score.confidence}; "
                f"+{len(score.major_positive_factors)}/-{len(score.major_negative_factors)}"
            ),
            status="complete",
        )
        session.add(section)
        session.flush()
        session.add(
            AuditMetric(
                id=new_uuid(),
                organisation_id=report.organisation_id,
                workspace_id=report.workspace_id,
                section_id=section.id,
                metric_key="confidence",
                metric_value=score.confidence,
                unit="ratio",
                label="Confidence",
            )
        )
        session.add(
            AuditMetric(
                id=new_uuid(),
                organisation_id=report.organisation_id,
                workspace_id=report.workspace_id,
                section_id=section.id,
                metric_key="inputs_used_count",
                metric_value=float(len(score.inputs_used)),
                unit="count",
                label="Inputs used",
            )
        )

    for finding in report.findings:
        if finding.severity == "info":
            continue
        session.add(
            AuditIssue(
                id=new_uuid(),
                organisation_id=report.organisation_id,
                workspace_id=report.workspace_id,
                audit_id=audit.id,
                code=finding.code,
                severity=finding.severity,
                title=finding.title,
                description=finding.description,
                evidence_url=finding.page_urls[0] if finding.page_urls else None,
                status="open",
            )
        )

    for rec in report.recommendations:
        session.add(
            AuditRecommendation(
                id=new_uuid(),
                organisation_id=report.organisation_id,
                workspace_id=report.workspace_id,
                audit_id=audit.id,
                title=rec.title,
                summary=(
                    f"{rec.reason}\n\nSuggested fix: {rec.suggested_fix}\n"
                    f"Affected: {', '.join(rec.affected_pages[:10])}"
                ),
                priority=rec.priority,
                impact_score=rec.impact,
                effort_score=rec.effort,
                status="proposed",
            )
        )

    session.add(
        SEOScore(
            id=new_uuid(),
            organisation_id=report.organisation_id,
            workspace_id=report.workspace_id,
            website_id=report.website_id,
            audit_id=audit.id,
            overall_score=report.peacock_seo_score.score,
            technical_score=report.scores.get("technical_seo").score if "technical_seo" in report.scores else None,
            onpage_score=report.scores.get("on_page_seo").score if "on_page_seo" in report.scores else None,
            content_score=report.scores.get("content_quality").score if "content_quality" in report.scores else None,
            authority_score=report.scores.get("internal_linking").score if "internal_linking" in report.scores else None,
            scored_at=now,
            status="active",
        )
    )
    session.commit()
    return audit
