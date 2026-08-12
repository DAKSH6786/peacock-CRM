from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, OrganisationScopedMixin, TimestampMixin


class Organisation(Base, TimestampMixin):
    __tablename__ = "organisations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    workspaces: Mapped[list[Workspace]] = relationship(
        back_populates="organisation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    memberships: Mapped[list[Membership]] = relationship(
        back_populates="organisation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    roles: Mapped[list[Role]] = relationship(
        back_populates="organisation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True)
    microsoft_sub: Mapped[str | None] = mapped_column(String(255), unique=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    memberships: Mapped[list[Membership]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    workspace_memberships: Mapped[list[WorkspaceMembership]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Workspace(Base, TimestampMixin, OrganisationScopedMixin):
    __tablename__ = "workspaces"
    __table_args__ = (UniqueConstraint("organisation_id", "slug"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organisation: Mapped[Organisation] = relationship(back_populates="workspaces")
    memberships: Mapped[list[WorkspaceMembership]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Role(Base, TimestampMixin, OrganisationScopedMixin):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("organisation_id", "code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    organisation: Mapped[Organisation] = relationship(back_populates="roles")
    permissions: Mapped[list[RolePermission]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    memberships: Mapped[list[Membership]] = relationship(back_populates="role")


class Permission(Base, TimestampMixin):
    """Global capability catalog (not tenant-scoped)."""

    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    role_links: Mapped[list[RolePermission]] = relationship(
        back_populates="permission",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class RolePermission(Base, TimestampMixin):
    """Many-to-many: org roles ↔ global permissions."""

    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    role_id: Mapped[str] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_id: Mapped[str] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[Role] = relationship(back_populates="permissions")
    permission: Mapped[Permission] = relationship(back_populates="role_links")


class Membership(Base, TimestampMixin, OrganisationScopedMixin):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("organisation_id", "user_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # RESTRICT: do not delete a role that is still assigned
    role_id: Mapped[str] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    user: Mapped[User] = relationship(back_populates="memberships")
    organisation: Mapped[Organisation] = relationship(back_populates="memberships")
    role: Mapped[Role] = relationship(back_populates="memberships")


class WorkspaceMembership(Base, TimestampMixin, OrganisationScopedMixin):
    __tablename__ = "workspace_memberships"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id: Mapped[str] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    organisation: Mapped[Organisation] = relationship()
    workspace: Mapped[Workspace] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="workspace_memberships")
    role: Mapped[Role] = relationship()
