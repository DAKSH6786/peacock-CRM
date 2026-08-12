from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db import get_db
from api.security import decode_token
from db_models import Membership, Organisation, Role, User, Workspace

bearer = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class AuthContext:
    user: User
    organisation: Organisation
    membership: Membership
    role_codes: list[str]
    workspace: Workspace | None


def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> AuthContext:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user_id = payload.get("sub")
    org_id = payload.get("org")
    if not user_id or not org_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")

    user = db.get(User, user_id)
    organisation = db.get(Organisation, org_id)
    if not user or not organisation or not user.is_active or not organisation.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive principal")

    membership = db.scalar(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.organisation_id == organisation.id,
        )
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No organisation membership")

    role = db.get(Role, membership.role_id)
    role_codes = [role.code] if role else []

    workspace = None
    ws_id = payload.get("ws")
    if ws_id:
        workspace = db.get(Workspace, ws_id)
        if workspace and workspace.organisation_id != organisation.id:
            # Hard tenant boundary — never leak cross-org workspace
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace tenant mismatch")

    return AuthContext(
        user=user,
        organisation=organisation,
        membership=membership,
        role_codes=role_codes,
        workspace=workspace,
    )


def require_roles(*allowed: str):
    def _dep(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if not set(ctx.role_codes) & set(allowed) and "owner" not in ctx.role_codes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return ctx

    return _dep
