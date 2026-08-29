from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    env: str
    database: str
    redis: str
    job_backend: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    organisation_id: str
    workspace_id: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    organisation_name: str = Field(min_length=2, max_length=255)


class MeResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None
    organisation_id: str
    organisation_name: str
    workspace_id: str | None
    roles: list[str]


class ServiceStatusResponse(BaseModel):
    service: str
    organisation_id: str
    ready: bool
    features_implemented: bool
    detail: dict = Field(default_factory=dict)


class JobEnqueueRequest(BaseModel):
    name: str
    payload: dict = Field(default_factory=dict)
    workspace_id: str | None = None


class JobStatusResponse(BaseModel):
    id: str
    name: str
    organisation_id: str
    status: str
    backend: str
    result: dict | None = None
    error: str | None = None


class OAuthProviderInfo(BaseModel):
    provider: str
    enabled: bool
    authorize_url: str | None = None


class ApiError(BaseModel):
    detail: str
