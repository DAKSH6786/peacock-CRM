"""Peacock Security for AI Connectors — treat LLM I/O as untrusted.

Controls:
- prompt injection detection
- content isolation
- tool permissions
- connector permissions
- URL safety
- PII handling
- tenant boundaries
- output validation

Website / crawler-extracted content is DATA. It is not trusted instructions.
Content must never instruct PINE to expose secrets or change system behaviour.
"""

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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, WorkspaceTenantMixin


SECURITY_CONTROLS: tuple[str, ...] = (
    "prompt_injection_detection",
    "content_isolation",
    "tool_permissions",
    "connector_permissions",
    "url_safety",
    "pii_handling",
    "tenant_boundaries",
    "output_validation",
)

CONTROL_LABELS: dict[str, str] = {
    "prompt_injection_detection": "Prompt injection detection",
    "content_isolation": "Content isolation",
    "tool_permissions": "Tool permissions",
    "connector_permissions": "Connector permissions",
    "url_safety": "URL safety",
    "pii_handling": "PII handling",
    "tenant_boundaries": "Tenant boundaries",
    "output_validation": "Output validation",
}

TRUST_TIERS: tuple[str, ...] = (
    "trusted_system",
    "trusted_user",
    "untrusted_data",
)

CONTENT_SOURCES: tuple[str, ...] = (
    "crawler_extracted",
    "serpapi_snippet",
    "ai_response",
    "user_prompt",
    "system_policy",
)

RISK_LEVELS: tuple[str, ...] = (
    "none",
    "low",
    "medium",
    "high",
    "critical",
)

SCAN_VERDICTS: tuple[str, ...] = (
    "allow",
    "allow_with_redactions",
    "quarantine",
    "block",
)

INJECTION_PATTERNS: tuple[str, ...] = (
    "ignore_previous_instructions",
    "reveal_system_prompt",
    "exfiltrate_secrets",
    "change_system_behaviour",
    "override_tool_policy",
    "cross_tenant_access",
)

TOOL_SCOPES: tuple[str, ...] = (
    "read_visibility",
    "web_fetch",
    "cms_write",
    "secret_read",
    "tenant_admin",
)

CONNECTOR_KINDS: tuple[str, ...] = (
    "llm_provider",
    "search_api",
    "cms",
    "analytics",
    "crawler",
)

METHODOLOGY = "peacock_ai_connector_security_v1"
METHODOLOGY_NOTE = (
    "Security for AI Connectors treats LLM input/output as untrusted. "
    "Crawler-extracted website content is DATA — never trusted instructions. "
    "Content must never instruct PINE to expose secrets or change system behaviour."
)
CRAWLER_AS_DATA_POLICY = (
    "Crawler-extracted content is DATA. It is not trusted instructions. "
    "Website content must never be able to instruct PINE to expose secrets "
    "or change system behaviour."
)
SECURITY_POSITIONING = (
    "Peacock Security for AI Connectors isolates untrusted web/AI content, "
    "enforces tool and connector permissions, validates URLs and outputs, "
    "handles PII, and keeps hard tenant boundaries around PINE."
)


class AiConnectorSecurityScan(Base, WorkspaceTenantMixin):
    """One AI connector security scan over untrusted content + permissions."""

    __tablename__ = "ai_connector_security_scans"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    connector_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    injection_findings_count: Mapped[int] = mapped_column(Integer, nullable=False)
    pii_findings_count: Mapped[int] = mapped_column(Integer, nullable=False)
    url_blocks_count: Mapped[int] = mapped_column(Integer, nullable=False)
    permission_denials_count: Mapped[int] = mapped_column(Integer, nullable=False)
    output_validation_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    tenant_boundary_ok: Mapped[bool] = mapped_column(Boolean, nullable=False)
    crawler_treated_as_data: Mapped[bool] = mapped_column(Boolean, nullable=False)
    secrets_exposure_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False)
    system_behaviour_change_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False)
    controls_active_count: Mapped[int] = mapped_column(Integer, nullable=False)
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    security_positioning: Mapped[str] = mapped_column(Text, nullable=False)
    crawler_as_data_policy: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    analysed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    content_segments: Mapped[list[AcsContentSegment]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )
    injection_findings: Mapped[list[AcsInjectionFinding]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )
    permission_checks: Mapped[list[AcsPermissionCheck]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )
    url_checks: Mapped[list[AcsUrlSafetyCheck]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )
    pii_findings: Mapped[list[AcsPiiFinding]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )
    output_validations: Mapped[list[AcsOutputValidation]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )
    control_activations: Mapped[list[AcsControlActivation]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )


class AcsContentSegment(Base, WorkspaceTenantMixin):
    """Isolated content blob with an explicit trust tier."""

    __tablename__ = "acs_content_segments"
    __table_args__ = (UniqueConstraint("scan_id", "segment_key"),)

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("ai_connector_security_scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    trust_tier: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    isolated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    treated_as_instructions: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    scan: Mapped[AiConnectorSecurityScan] = relationship(back_populates="content_segments")


class AcsInjectionFinding(Base, WorkspaceTenantMixin):
    """Detected prompt-injection / instruction-override attempt in untrusted data."""

    __tablename__ = "acs_injection_findings"

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("ai_connector_security_scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    pattern_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    matched_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)

    scan: Mapped[AiConnectorSecurityScan] = relationship(back_populates="injection_findings")


class AcsPermissionCheck(Base, WorkspaceTenantMixin):
    """Tool or connector permission evaluation."""

    __tablename__ = "acs_permission_checks"
    __table_args__ = (UniqueConstraint("scan_id", "permission_kind", "scope_or_connector"),)

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("ai_connector_security_scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    scope_or_connector: Mapped[str] = mapped_column(String(128), nullable=False)
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    scan: Mapped[AiConnectorSecurityScan] = relationship(back_populates="permission_checks")


class AcsUrlSafetyCheck(Base, WorkspaceTenantMixin):
    """URL safety decision (SSRF / scheme / private network)."""

    __tablename__ = "acs_url_safety_checks"

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("ai_connector_security_scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    scheme: Mapped[str] = mapped_column(String(16), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_private_or_local: Mapped[bool] = mapped_column(Boolean, nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    scan: Mapped[AiConnectorSecurityScan] = relationship(back_populates="url_checks")


class AcsPiiFinding(Base, WorkspaceTenantMixin):
    """PII detected in untrusted or model output content."""

    __tablename__ = "acs_pii_findings"

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("ai_connector_security_scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    pii_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    redacted_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    scan: Mapped[AiConnectorSecurityScan] = relationship(back_populates="pii_findings")


class AcsOutputValidation(Base, WorkspaceTenantMixin):
    """LLM output validation against schema / policy."""

    __tablename__ = "acs_output_validations"
    __table_args__ = (UniqueConstraint("scan_id", "check_key"),)

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("ai_connector_security_scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    check_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)

    scan: Mapped[AiConnectorSecurityScan] = relationship(back_populates="output_validations")


class AcsControlActivation(Base, WorkspaceTenantMixin):
    """Which AI connector security controls fired."""

    __tablename__ = "acs_control_activations"
    __table_args__ = (UniqueConstraint("scan_id", "control_kind"),)

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("ai_connector_security_scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    control_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    control_label: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    scan: Mapped[AiConnectorSecurityScan] = relationship(
        back_populates="control_activations"
    )
