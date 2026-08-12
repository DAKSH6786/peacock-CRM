"""Mock research connector for Layer 3 — replace with live specialised providers."""

from __future__ import annotations

from intelligence.models import EvidenceItem, EvidenceKind


class MockResearchConnector:
    name = "mock_research"

    async def research(self, query: str, *, organisation_id: str) -> list[EvidenceItem]:
        return [
            EvidenceItem(
                code="research.mock.snippet",
                label="External research snippet",
                value=f"Mock research for: {query[:120]}",
                kind=EvidenceKind.RESEARCH,
                source=self.name,
                confidence=0.4,
                metadata={"organisation_id": organisation_id, "mock": True},
            )
        ]
