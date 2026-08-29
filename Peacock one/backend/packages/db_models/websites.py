from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, TimestampMixin, WorkspaceTenantMixin, new_uuid


class Website(Base, WorkspaceTenantMixin):
    """Customer website under management."""

    __tablename__ = "websites"
    __table_args__ = (UniqueConstraint("workspace_id", "primary_domain"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    root_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(128))
    locale: Mapped[str] = mapped_column(String(32), default="en-US", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Sparse product-specific flags only — not a substitute for typed columns
    extensions: Mapped[dict | None] = mapped_column(JSONB)

    domains: Mapped[list[Domain]] = relationship(
        back_populates="website", cascade="all, delete-orphan", passive_deletes=True
    )
    properties: Mapped[list[WebsiteProperty]] = relationship(
        back_populates="website", cascade="all, delete-orphan", passive_deletes=True
    )


class Domain(Base, TimestampMixin):
    __tablename__ = "domains"
    __table_args__ = (UniqueConstraint("website_id", "hostname"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hostname: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, index=True)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    website: Mapped[Website] = relationship(back_populates="domains")


class WebsiteProperty(Base, TimestampMixin):
    """Typed key/value configuration for a website (replaces free-form metadata bags)."""

    __tablename__ = "website_properties"
    __table_args__ = (UniqueConstraint("website_id", "key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str] = mapped_column(String(4000), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    website: Mapped[Website] = relationship(back_populates="properties")
