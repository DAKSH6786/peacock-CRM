"""Peacock One Quality Bar engine — assess module completeness gates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from db_models.quality_bar import (
    COMPLETENESS_VERDICTS,
    GATE_IMPROVEMENTS,
    GATE_LABELS,
    GATE_PASS_MEANS,
    GATE_QUESTIONS,
    METHODOLOGY_NOTE,
    QUALITY_GATES,
    QUALITY_POSITIONING,
)


# Known Peacock modules with default gate answers (True = problem present / FAIL)
# answer_yes_problem=True means the "Does this merely…?" question is YES → fail gate
MODULE_CATALOG: dict[str, dict[str, Any]] = {
    "conventional_seo_auditor": {
        "label": "Conventional SEO auditor (anti-pattern)",
        "defaults": {
            "beyond_conventional_seo": True,
            "beyond_ai_mention_tracking": True,
            "evidence_backed_recommendations": True,
            "uncertainty_with_evidence": True,
            "outcome_tracking": True,
            "learning_loop": True,
            "deterministic_over_llm": False,
        },
        "notes": {
            "beyond_conventional_seo": "Classic crawl + rank factors only.",
            "beyond_ai_mention_tracking": "No generative visibility layer.",
            "evidence_backed_recommendations": "LLM tips without ledger evidence.",
            "uncertainty_with_evidence": "No confidence bands.",
            "outcome_tracking": "Recommendations never measured.",
            "learning_loop": "No Peacock Learning connection.",
            "deterministic_over_llm": "Scoring is already deterministic — pass.",
        },
    },
    "ai_mention_dashboard": {
        "label": "AI mention dashboard (anti-pattern)",
        "defaults": {
            "beyond_conventional_seo": False,
            "beyond_ai_mention_tracking": True,
            "evidence_backed_recommendations": True,
            "uncertainty_with_evidence": True,
            "outcome_tracking": True,
            "learning_loop": True,
            "deterministic_over_llm": False,
        },
        "notes": {
            "beyond_conventional_seo": "Touches AI surfaces.",
            "beyond_ai_mention_tracking": "Only counts mentions — improve toward SoA/CIS.",
            "evidence_backed_recommendations": "Mentions without evidence-backed actions.",
            "uncertainty_with_evidence": "No uncertainty.",
            "outcome_tracking": "No outcome loop.",
            "learning_loop": "No learning.",
            "deterministic_over_llm": "Counting is deterministic — pass.",
        },
    },
    "share_of_answer": {
        "label": "Share of Answer",
        "defaults": {
            "beyond_conventional_seo": False,
            "beyond_ai_mention_tracking": False,
            "evidence_backed_recommendations": False,
            "uncertainty_with_evidence": False,
            "outcome_tracking": False,
            "learning_loop": False,
            "deterministic_over_llm": False,
        },
        "notes": {
            "beyond_conventional_seo": "Generative influence, not classic SEO.",
            "beyond_ai_mention_tracking": "Multi-indicator influence, not mentions alone.",
            "evidence_backed_recommendations": "Indicators backed by observations.",
            "uncertainty_with_evidence": "Confidence on influence readings.",
            "outcome_tracking": "Outcomes via learning / moat pathways.",
            "learning_loop": "Feeds industry learning memory.",
            "deterministic_over_llm": "Influence math is deterministic.",
        },
    },
    "llm_only_recommender": {
        "label": "LLM-only recommender (anti-pattern)",
        "defaults": {
            "beyond_conventional_seo": False,
            "beyond_ai_mention_tracking": False,
            "evidence_backed_recommendations": True,
            "uncertainty_with_evidence": True,
            "outcome_tracking": True,
            "learning_loop": True,
            "deterministic_over_llm": True,
        },
        "notes": {
            "beyond_conventional_seo": "GEO-flavoured prompts.",
            "beyond_ai_mention_tracking": "Talks about citations.",
            "evidence_backed_recommendations": "Only LLM recommendation — add evidence.",
            "uncertainty_with_evidence": "No confidence — add it.",
            "outcome_tracking": "Never measures results — add outcome tracking.",
            "learning_loop": "Never learns — connect to Peacock Learning.",
            "deterministic_over_llm": "Uses LLM for score arithmetic — move out of LLM.",
        },
    },
    "research_mode": {
        "label": "Peacock Research Mode",
        "defaults": {
            "beyond_conventional_seo": False,
            "beyond_ai_mention_tracking": False,
            "evidence_backed_recommendations": False,
            "uncertainty_with_evidence": False,
            "outcome_tracking": False,
            "learning_loop": True,  # lab findings not yet auto-wired to learning
            "deterministic_over_llm": False,
        },
        "notes": {
            "beyond_conventional_seo": "Search intelligence laboratory.",
            "beyond_ai_mention_tracking": "Citation probability experiments.",
            "evidence_backed_recommendations": "Findings with evidence blocks.",
            "uncertainty_with_evidence": "Uncertainty bands required.",
            "outcome_tracking": "Baseline vs treatment deltas.",
            "learning_loop": "Connect lab findings to Peacock Learning.",
            "deterministic_over_llm": "Stats computed in code.",
        },
    },
    "custom": {
        "label": "Custom module",
        "defaults": {g: True for g in QUALITY_GATES},
        "notes": {g: "Provide gate answers explicitly." for g in QUALITY_GATES},
    },
}


REMEDIATION_TEMPLATES: dict[str, dict[str, str]] = {
    "beyond_conventional_seo": {
        "action_key": "add_generative_visibility",
        "action_label": "Add generative visibility capabilities",
        "detail": (
            "Move beyond crawl/rank SEO — add SoA, citation graph, entity gaps, "
            "or GEO experiments."
        ),
    },
    "beyond_ai_mention_tracking": {
        "action_key": "add_influence_metrics",
        "action_label": "Replace mention counts with influence metrics",
        "detail": (
            "Track Share of Answer, citation influence, retrieval pathways — "
            "not raw AI mention counts."
        ),
    },
    "evidence_backed_recommendations": {
        "action_key": "attach_evidence",
        "action_label": "Add evidence",
        "detail": "Bind every recommendation to Evidence Ledger / graph observations.",
    },
    "uncertainty_with_evidence": {
        "action_key": "add_confidence",
        "action_label": "Add confidence",
        "detail": "Pair evidence with confidence or uncertainty bands — no fake certainty.",
    },
    "outcome_tracking": {
        "action_key": "add_outcome_tracking",
        "action_label": "Add outcome tracking",
        "detail": "Measure recommendation → outcome deltas (moat pathways / learning).",
    },
    "learning_loop": {
        "action_key": "connect_peacock_learning",
        "action_label": "Connect to Peacock Learning",
        "detail": "Feed measured outcomes into Learning Engine 2.0 industry memory.",
    },
    "deterministic_over_llm": {
        "action_key": "move_out_of_llm",
        "action_label": "Move it out of the LLM",
        "detail": (
            "Compute deterministic scores/aggregations in code; reserve LLMs for "
            "judgment and synthesis (Cost Intelligence / Budget Engine)."
        ),
    },
}


@dataclass
class GateAnswer:
    gate_key: str
    # True = the problematic "yes" (merely/only/never) — gate FAILS
    answer_yes_problem: bool
    rationale: str | None = None
    evidence_note: str | None = None


@dataclass
class QualityBarSpec:
    client_brand: str
    module_key: str = "custom"
    module_label: str | None = None
    gate_answers: list[GateAnswer] = field(default_factory=list)
    analysed_at: datetime | None = None


@dataclass(slots=True)
class GateResultView:
    gate_key: str
    gate_label: str
    question: str
    improvement_if_fail: str
    passed: bool
    answer_yes_problem: bool
    rationale: str
    evidence_note: str | None
    rank_order: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RemediationActionView:
    gate_key: str
    action_key: str
    action_label: str
    detail: str
    links_to_learning: bool
    rank_order: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class QualityBarResult:
    client_brand: str
    module_key: str
    module_label: str
    completeness_verdict: str
    gates_total: int
    gates_passed: int
    gates_failed: int
    completeness_score: float
    blocked_by: list[str]
    improvement_summary: str
    gate_results: list[GateResultView]
    remediation_actions: list[RemediationActionView]
    quality_positioning: str
    methodology_note: str
    summary: str
    analysed_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_brand": self.client_brand,
            "module_key": self.module_key,
            "module_label": self.module_label,
            "completeness_verdict": self.completeness_verdict,
            "gates_total": self.gates_total,
            "gates_passed": self.gates_passed,
            "gates_failed": self.gates_failed,
            "completeness_score": self.completeness_score,
            "blocked_by": list(self.blocked_by),
            "improvement_summary": self.improvement_summary,
            "gate_results": [g.to_dict() for g in self.gate_results],
            "remediation_actions": [r.to_dict() for r in self.remediation_actions],
            "quality_positioning": self.quality_positioning,
            "methodology_note": self.methodology_note,
            "summary": self.summary,
            "analysed_at": self.analysed_at.isoformat(),
        }


def catalog() -> dict[str, Any]:
    return {
        "quality_gates": list(QUALITY_GATES),
        "gate_labels": dict(GATE_LABELS),
        "gate_questions": dict(GATE_QUESTIONS),
        "gate_improvements": dict(GATE_IMPROVEMENTS),
        "gate_pass_means": dict(GATE_PASS_MEANS),
        "completeness_verdicts": list(COMPLETENESS_VERDICTS),
        "module_catalog": {
            k: {"label": v["label"]} for k, v in MODULE_CATALOG.items()
        },
        "quality_positioning": QUALITY_POSITIONING,
        "methodology_note": METHODOLOGY_NOTE,
        "product_note": (
            "Peacock One Quality Bar — before any module is complete, clear all "
            "seven shipping gates."
        ),
        "checklist": [
            f"{GATE_QUESTIONS[g]} → {GATE_IMPROVEMENTS[g]}" for g in QUALITY_GATES
        ],
    }


def assess_quality_bar(spec: QualityBarSpec) -> QualityBarResult:
    brand = (spec.client_brand or "").strip()
    if not brand:
        raise ValueError("client_brand is required")

    module_key = (spec.module_key or "custom").strip().lower()
    if module_key not in MODULE_CATALOG:
        raise ValueError(f"Unsupported module_key: {module_key}")

    catalog_entry = MODULE_CATALOG[module_key]
    module_label = (spec.module_label or catalog_entry["label"]).strip()
    analysed_at = spec.analysed_at or datetime.now(tz=UTC)

    overrides = {a.gate_key: a for a in spec.gate_answers}
    for key in overrides:
        if key not in QUALITY_GATES:
            raise ValueError(f"Unsupported gate_key: {key}")

    gate_results: list[GateResultView] = []
    remediations: list[RemediationActionView] = []
    failed_keys: list[str] = []

    for i, gate in enumerate(QUALITY_GATES):
        if gate in overrides:
            yes_problem = bool(overrides[gate].answer_yes_problem)
            rationale = (
                overrides[gate].rationale
                or catalog_entry["notes"].get(gate)
                or GATE_PASS_MEANS[gate]
            )
            evidence_note = overrides[gate].evidence_note
        else:
            yes_problem = bool(catalog_entry["defaults"][gate])
            rationale = catalog_entry["notes"].get(gate) or GATE_PASS_MEANS[gate]
            evidence_note = None

        passed = not yes_problem
        if not passed:
            failed_keys.append(gate)
            tmpl = REMEDIATION_TEMPLATES[gate]
            remediations.append(
                RemediationActionView(
                    gate_key=gate,
                    action_key=tmpl["action_key"],
                    action_label=tmpl["action_label"],
                    detail=tmpl["detail"],
                    links_to_learning=(gate == "learning_loop"),
                    rank_order=len(remediations),
                )
            )

        gate_results.append(
            GateResultView(
                gate_key=gate,
                gate_label=GATE_LABELS[gate],
                question=GATE_QUESTIONS[gate],
                improvement_if_fail=GATE_IMPROVEMENTS[gate],
                passed=passed,
                answer_yes_problem=yes_problem,
                rationale=str(rationale),
                evidence_note=evidence_note,
                rank_order=i,
            )
        )

    total = len(QUALITY_GATES)
    passed_n = sum(1 for g in gate_results if g.passed)
    failed_n = total - passed_n
    score = round(100.0 * passed_n / total, 1)

    if failed_n == 0:
        verdict = "complete"
    elif passed_n == 0:
        verdict = "blocked"
    else:
        verdict = "incomplete"

    if remediations:
        improvement_summary = "; ".join(
            f"{GATE_QUESTIONS[r.gate_key]} → {GATE_IMPROVEMENTS[r.gate_key]}"
            for r in remediations
        )
    else:
        improvement_summary = (
            "All Quality Bar gates passed — module meets Peacock One shipping bar."
        )

    summary = (
        f"Quality Bar for {brand} / {module_label}: {verdict} "
        f"({passed_n}/{total} gates, score {score}). {QUALITY_POSITIONING}"
    )

    return QualityBarResult(
        client_brand=brand,
        module_key=module_key,
        module_label=module_label,
        completeness_verdict=verdict,
        gates_total=total,
        gates_passed=passed_n,
        gates_failed=failed_n,
        completeness_score=score,
        blocked_by=failed_keys,
        improvement_summary=improvement_summary,
        gate_results=gate_results,
        remediation_actions=remediations,
        quality_positioning=QUALITY_POSITIONING,
        methodology_note=METHODOLOGY_NOTE,
        summary=summary,
        analysed_at=analysed_at,
    )


def demo_assessment(brand: str = "Acme") -> QualityBarResult:
    """Demo: LLM-only recommender fails evidence/confidence/outcomes/learning/LLM misuse."""
    return assess_quality_bar(
        QualityBarSpec(client_brand=brand, module_key="llm_only_recommender")
    )
