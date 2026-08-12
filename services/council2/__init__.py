"""Peacock Council 2.0 — opposing-role multi-model debate."""

from db_models.council2 import (
    COUNCIL_ROLES,
    DEBATE_ROUNDS,
    FORBIDDEN_PROMPTS,
    FORBIDDEN_STORAGE_FIELDS,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    ROLE_MANDATES,
    STORED_ARTIFACT_KINDS,
)
from council2.debate import (
    ContextFact,
    CouncilBrief,
    assert_no_open_opinion_prompt,
    run_council_debate,
)
from council2.models import Council2Report, Council2Spec
from council2.service import Council2Service

__all__ = [
    "COUNCIL_ROLES",
    "DEBATE_ROUNDS",
    "FORBIDDEN_PROMPTS",
    "FORBIDDEN_STORAGE_FIELDS",
    "METHODOLOGY",
    "METHODOLOGY_NOTE",
    "ROLE_MANDATES",
    "STORED_ARTIFACT_KINDS",
    "ContextFact",
    "Council2Report",
    "Council2Service",
    "Council2Spec",
    "CouncilBrief",
    "assert_no_open_opinion_prompt",
    "run_council_debate",
]
