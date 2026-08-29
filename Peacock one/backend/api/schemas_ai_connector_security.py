"""Peacock Security for AI Connectors API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SecurityScanBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    connector_kind: str = Field(default="crawler", max_length=64)
    crawler_content: str = ""
    candidate_urls: list[str] = Field(default_factory=list)
    requested_tool_scopes: list[str] = Field(
        default_factory=lambda: ["read_visibility", "web_fetch"]
    )
    granted_tool_scopes: list[str] = Field(
        default_factory=lambda: ["read_visibility", "web_fetch"]
    )
    granted_connectors: list[str] = Field(
        default_factory=lambda: ["crawler", "llm_provider", "search_api"]
    )
    claimed_organisation_id: str | None = None
    model_output: str = ""
    analysed_at: datetime | None = None


class SecurityScanCreateRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: SecurityScanBriefRequest
    notes: str | None = None


class ContentSegmentResponse(BaseModel):
    segment_key: str
    source_kind: str
    trust_tier: str
    label: str
    excerpt: str
    isolated: bool
    treated_as_instructions: bool
    rank_order: int


class InjectionFindingResponse(BaseModel):
    segment_key: str
    pattern_key: str
    severity: str
    matched_excerpt: str
    blocked: bool
    rationale: str


class PermissionCheckResponse(BaseModel):
    permission_kind: str
    scope_or_connector: str
    allowed: bool
    reason: str
    rank_order: int


class UrlSafetyResponse(BaseModel):
    url: str
    scheme: str
    host: str
    is_private_or_local: bool
    decision: str
    reason: str


class PiiFindingResponse(BaseModel):
    segment_key: str
    pii_type: str
    action: str
    redacted_excerpt: str
    confidence: float


class OutputValidationResponse(BaseModel):
    check_key: str
    passed: bool
    detail: str


class ControlActivationResponse(BaseModel):
    control_kind: str
    control_label: str
    active: bool
    detail: str
    rank_order: int


class SecurityScanResponse(BaseModel):
    scan_id: str
    name: str
    client_brand: str
    methodology: str
    connector_kind: str
    risk_level: str
    verdict: str
    injection_findings_count: int
    pii_findings_count: int
    url_blocks_count: int
    permission_denials_count: int
    output_validation_passed: bool
    tenant_boundary_ok: bool
    crawler_treated_as_data: bool
    secrets_exposure_blocked: bool
    system_behaviour_change_blocked: bool
    controls_active_count: int
    content_segments: list[ContentSegmentResponse]
    injection_findings: list[InjectionFindingResponse]
    permission_checks: list[PermissionCheckResponse]
    url_checks: list[UrlSafetyResponse]
    pii_findings: list[PiiFindingResponse]
    output_validations: list[OutputValidationResponse]
    control_activations: list[ControlActivationResponse]
    security_positioning: str
    crawler_as_data_policy: str
    methodology_note: str
    summary: str
    analysed_at: str


class SecurityPreviewResponse(BaseModel):
    client_brand: str
    connector_kind: str
    risk_level: str
    verdict: str
    injection_findings_count: int
    pii_findings_count: int
    url_blocks_count: int
    permission_denials_count: int
    output_validation_passed: bool
    tenant_boundary_ok: bool
    crawler_treated_as_data: bool
    secrets_exposure_blocked: bool
    system_behaviour_change_blocked: bool
    controls_active_count: int
    content_segments: list[ContentSegmentResponse]
    injection_findings: list[InjectionFindingResponse]
    permission_checks: list[PermissionCheckResponse]
    url_checks: list[UrlSafetyResponse]
    pii_findings: list[PiiFindingResponse]
    output_validations: list[OutputValidationResponse]
    control_activations: list[ControlActivationResponse]
    security_positioning: str
    crawler_as_data_policy: str
    methodology_note: str
    summary: str
    analysed_at: str


class SecurityCatalogResponse(BaseModel):
    security_controls: list[str]
    control_labels: dict[str, str]
    trust_tiers: list[str]
    content_sources: list[str]
    risk_levels: list[str]
    scan_verdicts: list[str]
    injection_patterns: list[str]
    tool_scopes: list[str]
    connector_kinds: list[str]
    crawler_as_data_policy: str
    security_positioning: str
    methodology_note: str
    product_note: str
    example_blocked: str
