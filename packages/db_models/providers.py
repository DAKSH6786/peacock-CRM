from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, TimestampMixin


class AiProvider(Base, TimestampMixin):
    """Platform catalog of supported LLM / answer-engine providers.

    Global (not organisation-scoped). Org credentials belong in a future
    encrypted credentials table — never store API keys here.
    """

    __tablename__ = "ai_providers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    vendor: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_chat: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_embeddings: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_web_grounding: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    documentation_url: Mapped[str | None] = mapped_column(String(512))
    notes: Mapped[str | None] = mapped_column(Text)

    models: Mapped[list[AiProviderModel]] = relationship(
        back_populates="provider",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AiProviderModel(Base, TimestampMixin):
    """Known models offered by a provider (relational, not JSON arrays)."""

    __tablename__ = "ai_provider_models"
    __table_args__ = (UniqueConstraint("provider_id", "model_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    provider_id: Mapped[str] = mapped_column(
        ForeignKey("ai_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_code: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    context_window_tokens: Mapped[int | None] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    provider: Mapped[AiProvider] = relationship(back_populates="models")
