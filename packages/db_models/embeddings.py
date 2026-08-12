from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db_models.base import Base, OrganisationScopedMixin, TimestampMixin

# Default embedding dimensionality — adjustable per model via metadata
EMBEDDING_DIMENSIONS = 1536


class EmbeddingChunk(Base, TimestampMixin, OrganisationScopedMixin):
    """pgvector-backed embeddings — no separate vector database."""

    __tablename__ = "embedding_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id"), nullable=False, index=True
    )
    workspace_id: Mapped[str | None] = mapped_column(String(36), index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=True)
    # Structured evidence / decision traces only — never private chain-of-thought
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
