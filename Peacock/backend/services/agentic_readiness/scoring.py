"""Agentic Web Readiness scoring — Agent Discoverability → Agent Readiness Score."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from db_models.agentic_readiness import (
    CHECK_LABELS,
    DISCOVERABILITY_CHECKS,
    METHODOLOGY_NOTE,
    NOT_INDUSTRY_STANDARD,
    SURFACE_SEPARATION,
)


# Default weights — commerce/service machine-operability (not SEO/AEO/GEO weights)
_DEFAULT_WEIGHTS: dict[str, float] = {
    "structured_product_information": 1.2,
    "clear_pricing": 1.2,
    "availability": 1.0,
    "product_ids": 1.0,
    "schema": 1.1,
    "api_discoverability": 1.3,
    "machine_readable_policies": 0.9,
    "service_descriptions": 0.9,
    "locations": 0.8,
    "booking_information": 1.0,
    "contact_mechanisms": 0.9,
    "returns": 0.8,
    "shipping": 0.8,
    "trust_signals": 0.9,
}

PASS_THRESHOLD = 60.0


def _clamp100(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _band(score: float) -> str:
    if score < 35:
        return "nascent"
    if score < 55:
        return "emerging"
    if score < 75:
        return "operable"
    return "agent_ready"


@dataclass
class CheckSignal:
    """Observed signal strength for one discoverability check (0–100)."""

    check_code: str
    score: float
    evidence_summary: str = ""
    machine_operable_signal: str | None = None

    def validate(self) -> None:
        if self.check_code not in DISCOVERABILITY_CHECKS:
            raise ValueError(f"Unknown check_code: {self.check_code}")
        if not (0.0 <= self.score <= 100.0):
            raise ValueError("check score must be 0–100")


@dataclass
class ReadinessSpec:
    client_brand: str
    industry: str | None = None
    signals: list[CheckSignal] = field(default_factory=list)
    # If empty, use neutral priors (not fake perfection)
    business_type: str = "mixed"  # commerce|services|mixed


@dataclass(slots=True)
class CheckResult:
    check_code: str
    check_label: str
    score: float
    weight: float
    passed: bool
    evidence_summary: str
    machine_operable_signal: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class GapResult:
    check_code: str
    title: str
    severity: str
    recommendation: str
    priority: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReadinessAnalysisResult:
    agent_readiness_score: float
    readiness_band: str
    checks: list[CheckResult]
    gaps: list[GapResult]
    checks_passed: int
    checks_total: int
    separate_from_seo_aeo_geo: bool
    surface_separation_note: str
    not_industry_standard: bool
    not_industry_standard_note: str
    methodology_note: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_readiness_score": self.agent_readiness_score,
            "readiness_band": self.readiness_band,
            "checks": [c.to_dict() for c in self.checks],
            "gaps": [g.to_dict() for g in self.gaps],
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
            "separate_from_seo_aeo_geo": self.separate_from_seo_aeo_geo,
            "surface_separation_note": self.surface_separation_note,
            "not_industry_standard": self.not_industry_standard,
            "not_industry_standard_note": self.not_industry_standard_note,
            "methodology_note": self.methodology_note,
            "summary": self.summary,
        }


def _neutral_priors(business_type: str) -> dict[str, float]:
    """Conservative priors when signals are omitted — avoid fake high scores."""
    base = {code: 45.0 for code in DISCOVERABILITY_CHECKS}
    if business_type == "commerce":
        base["structured_product_information"] = 50.0
        base["clear_pricing"] = 50.0
        base["product_ids"] = 48.0
        base["returns"] = 45.0
        base["shipping"] = 45.0
        base["booking_information"] = 25.0
    elif business_type == "services":
        base["service_descriptions"] = 55.0
        base["booking_information"] = 50.0
        base["locations"] = 50.0
        base["structured_product_information"] = 30.0
        base["product_ids"] = 25.0
        base["shipping"] = 20.0
        base["returns"] = 20.0
    return base


def _gap_recommendation(check_code: str) -> str:
    recs = {
        "structured_product_information": (
            "Expose structured product attributes (name, variants, specs) in "
            "machine-readable form agents can parse."
        ),
        "clear_pricing": "Publish unambiguous prices (currency, tax context) agents can extract.",
        "availability": "Surface stock/availability states in structured or API form.",
        "product_ids": "Provide stable product IDs (SKU/GTIN/MPN) consistently.",
        "schema": "Add relevant structured data (Product/Offer/Organization/Service) where accurate.",
        "api_discoverability": (
            "Publish discoverable API docs, OpenAPI, or well-known endpoints for agents."
        ),
        "machine_readable_policies": (
            "Provide machine-readable policy pages (terms, privacy) with clear structure."
        ),
        "service_descriptions": "Describe services with explicit scope, outcomes, and constraints.",
        "locations": "Publish structured location data (addresses, geo, hours).",
        "booking_information": "Expose booking slots, requirements, or reservation endpoints.",
        "contact_mechanisms": "Provide explicit contact channels agents can hand off to.",
        "returns": "Document return windows and conditions in structured policy form.",
        "shipping": "Expose shipping methods, regions, and ETA signals clearly.",
        "trust_signals": "Surface verifiable trust cues (reviews schema, certifications, identity).",
    }
    return recs.get(check_code, "Improve machine-operable signals for this check.")


def analyse_readiness(spec: ReadinessSpec) -> ReadinessAnalysisResult:
    """Compute Agent Readiness Score from Agent Discoverability checks."""
    if not spec.client_brand.strip():
        raise ValueError("client_brand is required")
    if spec.business_type not in ("commerce", "services", "mixed"):
        raise ValueError("business_type must be commerce|services|mixed")

    signal_map = {s.check_code: s for s in spec.signals}
    for s in spec.signals:
        s.validate()

    priors = _neutral_priors(spec.business_type)
    checks: list[CheckResult] = []
    weighted_sum = 0.0
    weight_total = 0.0

    for code in DISCOVERABILITY_CHECKS:
        weight = _DEFAULT_WEIGHTS[code]
        if code in signal_map:
            sig = signal_map[code]
            score = _clamp100(sig.score)
            evidence = sig.evidence_summary or f"Observed signal for {CHECK_LABELS[code]}."
            mos = sig.machine_operable_signal
        else:
            score = priors[code]
            evidence = (
                f"No explicit signal supplied; using conservative prior "
                f"({score:.0f}/100) for {CHECK_LABELS[code]}."
            )
            mos = None
        passed = score >= PASS_THRESHOLD
        checks.append(
            CheckResult(
                check_code=code,
                check_label=CHECK_LABELS[code],
                score=round(score, 1),
                weight=weight,
                passed=passed,
                evidence_summary=evidence,
                machine_operable_signal=mos,
            )
        )
        weighted_sum += score * weight
        weight_total += weight

    agent_score = round(weighted_sum / max(weight_total, 1e-6), 1)
    band = _band(agent_score)
    passed_n = sum(1 for c in checks if c.passed)

    gaps: list[GapResult] = []
    failing = sorted(
        [c for c in checks if not c.passed],
        key=lambda c: (c.score, -c.weight),
    )
    for i, c in enumerate(failing, start=1):
        severity = "high" if c.score < 40 else "medium" if c.score < PASS_THRESHOLD else "low"
        gaps.append(
            GapResult(
                check_code=c.check_code,
                title=f"Weak {c.check_label.lower()}",
                severity=severity,
                recommendation=_gap_recommendation(c.check_code),
                priority=i,
            )
        )

    summary = (
        f"Agent Readiness Score for {spec.client_brand}: {agent_score}/100 ({band}). "
        f"{passed_n}/{len(checks)} Agent Discoverability checks passed. "
        f"{SURFACE_SEPARATION} {NOT_INDUSTRY_STANDARD}"
    )

    return ReadinessAnalysisResult(
        agent_readiness_score=agent_score,
        readiness_band=band,
        checks=checks,
        gaps=gaps,
        checks_passed=passed_n,
        checks_total=len(checks),
        separate_from_seo_aeo_geo=True,
        surface_separation_note=SURFACE_SEPARATION,
        not_industry_standard=True,
        not_industry_standard_note=NOT_INDUSTRY_STANDARD,
        methodology_note=METHODOLOGY_NOTE,
        summary=summary,
    )
