"""AEO engine — answer-readiness analysis over crawled pages."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from aeo_engine.scoring import PageAeoScore, aggregate_scores, analyse_page
from db_models.base import new_uuid
from db_models.crawls import Crawl, CrawlPage
from db_models.geo_aeo import AEOObservation


@dataclass(slots=True)
class AeoEngine:
    organisation_id: str

    def status(self) -> dict[str, Any]:
        return {
            "service": "aeo_engine",
            "organisation_id": self.organisation_id,
            "ready": True,
            "features_implemented": True,
            "scoring": "deterministic",
            "persists_to": "aeo_observations",
            "honesty": (
                "AEO analyses crawled page content for answerability, FAQ coverage, "
                "citation readiness, entity/question coverage. Scores are proprietary "
                "deterministic estimates — not live answer-engine rankings."
            ),
        }


class AeoAnalysisService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def analyse_crawl(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        website_id: str,
        crawl_id: str,
        name: str,
        page_urls: list[str] | None = None,
        created_by: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        crawl = self.db.get(Crawl, crawl_id)
        if crawl is None or crawl.organisation_id != organisation_id:
            raise LookupError("Crawl not found")
        if crawl.website_id and crawl.website_id != website_id:
            raise ValueError("website_id does not match crawl")

        pages = list(
            self.db.scalars(
                select(CrawlPage).where(CrawlPage.crawl_id == crawl_id)
            )
        )
        if page_urls:
            wanted = {u.rstrip("/") for u in page_urls}
            pages = [p for p in pages if (p.url or "").rstrip("/") in wanted]
        if not pages:
            raise ValueError("No crawl pages available for AEO analysis")

        scored: list[PageAeoScore] = []
        for page in pages:
            scored.append(
                analyse_page(
                    {
                        "url": page.url,
                        "title": page.title,
                        "meta_description": page.meta_description,
                        "h1": page.h1,
                        "h2": page.h2,
                        "h3": page.h3,
                        "body_text": page.body_text,
                        "word_count": page.word_count,
                        "schema_blocks": page.schema_blocks,
                        "external_links": page.external_links,
                        "canonical": getattr(page, "canonical_url", None) or getattr(page, "canonical", None),
                    }
                )
            )

        aggregates = aggregate_scores(scored)
        analysis_id = new_uuid()
        payload = {
            "analysis_id": analysis_id,
            "name": name,
            "crawl_id": crawl_id,
            "website_id": website_id,
            "page_count": len(scored),
            "pages": [p.to_dict() for p in scored],
            "recommendations": _dedupe(
                [r for p in scored for r in p.recommendations]
            ),
            "notes": notes,
            "created_by": created_by,
            "analysed_at": datetime.now(UTC).isoformat(),
            **aggregates,
        }
        row = AEOObservation(
            id=analysis_id,
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=website_id,
            observation_id=None,
            answerability_score=aggregates["answerability_score"],
            faq_coverage_score=aggregates["faq_coverage_score"],
            citation_readiness_score=aggregates["citation_readiness_score"],
            notes=json.dumps(payload, sort_keys=True),
        )
        self.db.add(row)
        self.db.commit()
        return payload

    def get_analysis(self, *, organisation_id: str, analysis_id: str) -> dict[str, Any] | None:
        row = self.db.get(AEOObservation, analysis_id)
        if row is None or row.organisation_id != organisation_id:
            return None
        if row.notes:
            try:
                data = json.loads(row.notes)
                if isinstance(data, dict) and data.get("analysis_id"):
                    return data
            except json.JSONDecodeError:
                pass
        return {
            "analysis_id": row.id,
            "website_id": row.website_id,
            "answerability_score": row.answerability_score,
            "faq_coverage_score": row.faq_coverage_score,
            "citation_readiness_score": row.citation_readiness_score,
            "notes": row.notes,
        }


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))
