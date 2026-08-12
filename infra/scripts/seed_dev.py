#!/usr/bin/env python3
"""Seed local development organisation + admin user."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "apps" / "api"), str(ROOT / "services"), str(ROOT / "packages")]

from sqlalchemy import select

from api.config import get_settings
from api.db import SessionLocal
from api.security import hash_password
from db_models import Membership, Organisation, Role, User, Workspace


def main() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == settings.seed_admin_email.lower()))
        if existing:
            print(f"Seed already present for {settings.seed_admin_email}")
            return

        org_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        role_id = str(uuid.uuid4())
        workspace_id = str(uuid.uuid4())

        org = Organisation(id=org_id, name=settings.seed_org_name, slug=settings.seed_org_slug)
        user = User(
            id=user_id,
            email=settings.seed_admin_email.lower(),
            full_name="Peacock Admin",
            hashed_password=hash_password(settings.seed_admin_password),
            is_email_verified=True,
        )
        role = Role(id=role_id, organisation_id=org_id, code="owner", name="Owner")
        workspace = Workspace(
            id=workspace_id,
            organisation_id=org_id,
            name="Default",
            slug="default",
        )
        membership = Membership(
            id=str(uuid.uuid4()),
            organisation_id=org_id,
            user_id=user_id,
            role_id=role_id,
        )
        db.add_all([org, user, role, workspace, membership])
        db.commit()
        print(f"Seeded org={org.slug} admin={user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
