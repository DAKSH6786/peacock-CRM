#!/usr/bin/env python3
"""Seed local development organisation, admin user, and AI provider catalog."""

from __future__ import annotations

import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "apps" / "api"), str(ROOT / "services"), str(ROOT / "packages")]

from sqlalchemy import select

from api.config import get_settings
from api.db import SessionLocal
from api.security import hash_password
from db_models import (
    AiProvider,
    AiProviderModel,
    GenerativeEngine,
    Membership,
    Organisation,
    Permission,
    Role,
    RolePermission,
    User,
    Workspace,
)
from db_models.generative_engine_seed import GENERATIVE_ENGINE_SEEDS
from db_models.provider_seed import SUPPORTED_AI_PROVIDERS


def seed_ai_providers(db) -> int:
    """Idempotently upsert the five supported AI providers + models."""
    created = 0
    now = datetime.now(UTC)
    for spec in SUPPORTED_AI_PROVIDERS:
        provider = db.scalar(select(AiProvider).where(AiProvider.code == spec.code))
        if provider is None:
            provider = AiProvider(
                id=str(uuid.uuid4()),
                code=spec.code,
                name=spec.name,
                vendor=spec.vendor,
                is_active=True,
                supports_chat=spec.supports_chat,
                supports_embeddings=spec.supports_embeddings,
                supports_web_grounding=spec.supports_web_grounding,
                documentation_url=spec.documentation_url,
                notes=spec.notes,
                created_at=now,
                updated_at=now,
            )
            db.add(provider)
            created += 1
        else:
            provider.name = spec.name
            provider.vendor = spec.vendor
            provider.is_active = True
            provider.supports_chat = spec.supports_chat
            provider.supports_embeddings = spec.supports_embeddings
            provider.supports_web_grounding = spec.supports_web_grounding
            provider.documentation_url = spec.documentation_url
            provider.notes = spec.notes
            provider.updated_at = now

        db.flush()
        for model_spec in spec.models:
            existing = db.scalar(
                select(AiProviderModel).where(
                    AiProviderModel.provider_id == provider.id,
                    AiProviderModel.model_code == model_spec.model_code,
                )
            )
            if existing is None:
                db.add(
                    AiProviderModel(
                        id=str(uuid.uuid4()),
                        provider_id=provider.id,
                        model_code=model_spec.model_code,
                        display_name=model_spec.display_name,
                        is_default=model_spec.is_default,
                        is_active=True,
                        context_window_tokens=model_spec.context_window_tokens,
                        sort_order=model_spec.sort_order,
                        created_at=now,
                        updated_at=now,
                    )
                )
            else:
                existing.display_name = model_spec.display_name
                existing.is_default = model_spec.is_default
                existing.is_active = True
                existing.context_window_tokens = model_spec.context_window_tokens
                existing.sort_order = model_spec.sort_order
                existing.updated_at = now
    return created


def seed_generative_engines(db) -> int:
    """Idempotently upsert generative / answer engines linked to AI providers."""
    created = 0
    now = datetime.now(UTC)
    providers = {
        p.code: p for p in db.scalars(select(AiProvider)).all()
    }
    for spec in GENERATIVE_ENGINE_SEEDS:
        existing = db.scalar(select(GenerativeEngine).where(GenerativeEngine.code == spec.code))
        provider = providers.get(spec.provider_code) if spec.provider_code else None
        if existing is None:
            db.add(
                GenerativeEngine(
                    id=str(uuid.uuid4()),
                    code=spec.code,
                    name=spec.name,
                    vendor=spec.vendor,
                    llm_provider_id=provider.id if provider else None,
                    is_active=True,
                    status="active",
                    created_at=now,
                    updated_at=now,
                )
            )
            created += 1
        else:
            existing.name = spec.name
            existing.vendor = spec.vendor
            existing.llm_provider_id = provider.id if provider else None
            existing.is_active = True
            existing.status = "active"
            existing.updated_at = now
    return created


def seed_capability_priors(db) -> int:
    """Upsert soft model capability priors — defaults only, not permanent locks."""
    from capability_router import CapabilityProfileRepository

    return CapabilityProfileRepository(db).seed_soft_priors()


def seed_standard_roles(db, organisation_id: str) -> dict[str, str]:
    """Ensure owner/admin/editor/viewer roles exist for an organisation."""
    now = datetime.now(UTC)
    wanted = {
        "owner": "Owner",
        "admin": "Admin",
        "editor": "Editor",
        "viewer": "Viewer",
    }
    ids: dict[str, str] = {}
    for code, name in wanted.items():
        role = db.scalar(
            select(Role).where(Role.organisation_id == organisation_id, Role.code == code)
        )
        if role is None:
            role = Role(
                id=str(uuid.uuid4()),
                organisation_id=organisation_id,
                code=code,
                name=name,
                created_at=now,
                updated_at=now,
            )
            db.add(role)
            db.flush()
        ids[code] = role.id
    return ids


def seed_permissions(db) -> None:
    now = datetime.now(UTC)
    catalog = [
        ("intelligence:view", "View generative visibility intelligence"),
        ("intelligence:run", "Run cognitive intelligence pipelines"),
        ("intelligence:manage", "Manage visibility properties and strategies"),
        ("settings:manage", "Manage organisation settings"),
        ("audit:view", "View audit logs"),
    ]
    for code, description in catalog:
        existing = db.scalar(select(Permission).where(Permission.code == code))
        if existing is None:
            db.add(
                Permission(
                    id=str(uuid.uuid4()),
                    code=code,
                    description=description,
                    created_at=now,
                    updated_at=now,
                )
            )


def seed_admin(db, settings) -> None:
    existing = db.scalar(select(User).where(User.email == settings.seed_admin_email.lower()))
    if existing:
        # Ensure standard roles exist for the user's organisation(s).
        memberships = list(
            db.scalars(select(Membership).where(Membership.user_id == existing.id)).all()
        )
        for membership in memberships:
            seed_standard_roles(db, membership.organisation_id)
        print(f"Admin already present for {settings.seed_admin_email}")
        return

    now = datetime.now(UTC)
    org_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())

    org = Organisation(
        id=org_id,
        name=settings.seed_org_name,
        slug=settings.seed_org_slug,
        created_at=now,
        updated_at=now,
    )
    user = User(
        id=user_id,
        email=settings.seed_admin_email.lower(),
        full_name="Peacock Admin",
        hashed_password=hash_password(settings.seed_admin_password),
        is_email_verified=True,
        created_at=now,
        updated_at=now,
    )
    role_ids = seed_standard_roles(db, org_id)
    role_id = role_ids["owner"]
    workspace = Workspace(
        id=workspace_id,
        organisation_id=org_id,
        name="Default",
        slug="default",
        created_at=now,
        updated_at=now,
    )
    membership = Membership(
        id=str(uuid.uuid4()),
        organisation_id=org_id,
        user_id=user_id,
        role_id=role_id,
        created_at=now,
        updated_at=now,
    )
    db.add_all([org, user, workspace, membership])
    db.flush()

    permissions = list(db.scalars(select(Permission)).all())
    for permission in permissions:
        db.add(
            RolePermission(
                id=str(uuid.uuid4()),
                role_id=role_id,
                permission_id=permission.id,
                created_at=now,
                updated_at=now,
            )
        )
    print(f"Seeded org={org.slug} admin={user.email}")


def main() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        seed_permissions(db)
        created = seed_ai_providers(db)
        engines_created = seed_generative_engines(db)
        priors_touched = seed_capability_priors(db)
        seed_admin(db, settings)
        db.commit()
        print(f"AI providers upserted (new rows created this run: {created})")
        print(f"Generative engines upserted (new rows: {engines_created})")
        print(f"Capability soft priors created this run: {priors_touched}")
        print(f"Supported provider codes: {[p.code for p in SUPPORTED_AI_PROVIDERS]}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
