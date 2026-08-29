"""Manual/Draft connector — the safe default. Never calls an external CMS.

Always requires explicit confirmation, and even then only marks the content
as "ready for manual publish" (e.g. copy-paste into a CMS by a human) — it
never pushes content anywhere automatically.
"""

from __future__ import annotations

from peacock_publishing.models import PublishRequest, PublishResult


class ManualApprovalConnector:
    name = "manual"

    def is_configured(self) -> bool:
        return True  # always available — the safe fallback

    async def publish(self, request: PublishRequest, *, confirm: bool) -> PublishResult:
        if not confirm:
            return PublishResult(
                connector=self.name,
                published=False,
                status="requires_confirmation",
                detail="Set confirm=true to mark this content ready for manual publishing.",
            )
        return PublishResult(
            connector=self.name,
            published=False,
            status="draft_created",
            detail=(
                f"'{request.title}' is ready for manual publishing. Peacock does not publish "
                "automatically — copy this content into your CMS when you're ready."
            ),
        )
