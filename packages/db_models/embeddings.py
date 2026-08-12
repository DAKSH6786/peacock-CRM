from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, OrganisationScopedMixin, TimestampMixin

EMBEDDING_DIMENSIONS = 1536


class EmbeddingChunk(Base, TimestampMixin, OrganisationScopedMixin):
    """pgvector-backed embeddings with relational metadata (no JSONB bag)."""

    __tablename__ = "embedding_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[str | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    embedding_model: Mapped[str | None] = mapped_column(String(128))
    token_count: Mapped[int | None] = mapped_column(Integer)
    embedding = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=True)

    organisation = relationship("Organisation")
    workspace = relationship("Workspace")
    attributes: Mapped[list[EmbeddingChunkAttribute]] = relationship(
        back_populates="chunk",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class EmbeddingChunkAttribute(Base, TimestampMixin):
    """Sparse typed attributes for chunks (labels, locale, section, …)."""

    __tablename__ = "embedding_chunk_attributes"
    __table_args__ = (UniqueConstraint("chunk_id", "key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chunk_id: Mapped[str] = mapped_column(
        ForeignKey("embedding_chunks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str] = mapped_column(String(2000), nullable=False)

    chunk: Mapped[EmbeddingChunk] = relationship(back_populates="attributes")
