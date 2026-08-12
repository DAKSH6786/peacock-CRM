from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.config import get_settings
from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas import (
    LoginRequest,
    MeResponse,
    OAuthProviderInfo,
    RegisterRequest,
    TokenResponse,
)
from api.security import create_access_token, hash_password, verify_password
from db_models import Membership, Organisation, Role, User, Workspace
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/auth", tags=["auth"])
audit = AuditLogger()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.scalar(select(User).where(User.email == body.email.lower()))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    org_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    role_id = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())
    membership_id = str(uuid.uuid4())

    slug_base = "".join(ch.lower() if ch.isalnum() else "-" for ch in body.organisation_name).strip("-")
    slug = slug_base or f"org-{org_id[:8]}"

    organisation = Organisation(id=org_id, name=body.organisation_name, slug=slug)
    user = User(
        id=user_id,
        email=body.email.lower(),
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        is_email_verified=False,
    )
    role = Role(id=role_id, organisation_id=org_id, code="owner", name="Owner")
    workspace = Workspace(
        id=workspace_id,
        organisation_id=org_id,
        name="Default",
        slug="default",
    )
    membership = Membership(
        id=membership_id,
        organisation_id=org_id,
        user_id=user_id,
        role_id=role_id,
    )

    db.add_all([organisation, user, role, workspace, membership])
    db.commit()

    audit.log(
        AuditEvent(
            organisation_id=org_id,
            actor_user_id=user_id,
            action="auth.register",
            resource_type="organisation",
            resource_id=org_id,
        )
    )

    token = create_access_token(
        subject=user_id,
        organisation_id=org_id,
        workspace_id=workspace_id,
        roles=["owner"],
    )
    return TokenResponse(
        access_token=token,
        organisation_id=org_id,
        workspace_id=workspace_id,
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    membership = db.scalar(select(Membership).where(Membership.user_id == user.id))
    if not membership:
        raise HTTPException(status_code=403, detail="No organisation membership")

    role = db.get(Role, membership.role_id)
    workspace = db.scalar(
        select(Workspace).where(Workspace.organisation_id == membership.organisation_id)
    )

    audit.log(
        AuditEvent(
            organisation_id=membership.organisation_id,
            actor_user_id=user.id,
            action="auth.login",
            resource_type="user",
            resource_id=user.id,
        )
    )

    token = create_access_token(
        subject=user.id,
        organisation_id=membership.organisation_id,
        workspace_id=workspace.id if workspace else None,
        roles=[role.code] if role else [],
    )
    return TokenResponse(
        access_token=token,
        organisation_id=membership.organisation_id,
        workspace_id=workspace.id if workspace else None,
    )


@router.get("/me", response_model=MeResponse)
def me(ctx: AuthContext = Depends(get_auth_context)) -> MeResponse:
    return MeResponse(
        id=ctx.user.id,
        email=ctx.user.email,
        full_name=ctx.user.full_name,
        organisation_id=ctx.organisation.id,
        organisation_name=ctx.organisation.name,
        workspace_id=ctx.workspace.id if ctx.workspace else None,
        roles=ctx.role_codes,
    )


@router.get("/oauth/providers", response_model=list[OAuthProviderInfo])
def oauth_providers() -> list[OAuthProviderInfo]:
    """Prepared OAuth surface — Google/Microsoft wired when secrets are present."""
    settings = get_settings()
    return [
        OAuthProviderInfo(
            provider="google",
            enabled=bool(settings.google_oauth_client_id and settings.google_oauth_client_secret),
            authorize_url=(
                f"{settings.oauth_redirect_base_url}/auth/oauth/google/start"
                if settings.google_oauth_client_id
                else None
            ),
        ),
        OAuthProviderInfo(
            provider="microsoft",
            enabled=bool(
                settings.microsoft_oauth_client_id and settings.microsoft_oauth_client_secret
            ),
            authorize_url=(
                f"{settings.oauth_redirect_base_url}/auth/oauth/microsoft/start"
                if settings.microsoft_oauth_client_id
                else None
            ),
        ),
        OAuthProviderInfo(provider="email_password", enabled=True, authorize_url=None),
    ]


@router.get("/oauth/{provider}/start")
def oauth_start(provider: str) -> dict:
    if provider not in {"google", "microsoft"}:
        raise HTTPException(status_code=404, detail="Unknown provider")
    settings = get_settings()
    enabled = (
        settings.google_oauth_client_id
        if provider == "google"
        else settings.microsoft_oauth_client_id
    )
    if not enabled:
        raise HTTPException(status_code=501, detail=f"{provider} OAuth is not configured")
    return {
        "detail": f"{provider} OAuth start is prepared but not fully implemented in architecture stage",
        "provider": provider,
    }
