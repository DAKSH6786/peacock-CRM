"""Peacock AI Agents — modular, read-only analysts and draft-preparers.

    SEO Agent, AEO Agent, GEO Agent, Research Agent, Content Strategist Agent,
    Competitor Agent, Citation Agent, Internal Linking Agent, Technical SEO
    Agent, Content Refresh Agent, Measurement Agent, Experiment Agent.

Every agent analyses real data already computed by Peacock's engines and
returns findings/recommendations/tasks/drafts. No agent publishes, deletes,
or modifies a production system — see ``AGENT_GUARDRAIL_NOTE``.
"""

from peacock_agents.aeo_agent import run_aeo_agent
from peacock_agents.citation_agent import run_citation_agent
from peacock_agents.competitor_agent import run_competitor_agent
from peacock_agents.content_refresh_agent import run_content_refresh_agent
from peacock_agents.content_strategist_agent import run_content_strategist_agent
from peacock_agents.experiment_agent import run_experiment_agent
from peacock_agents.geo_agent import run_geo_agent
from peacock_agents.internal_linking_agent import run_internal_linking_agent
from peacock_agents.measurement_agent import run_measurement_agent
from peacock_agents.models import AGENT_GUARDRAIL_NOTE, AgentDraft, AgentResult, AgentTask
from peacock_agents.research_agent import run_research_agent
from peacock_agents.seo_agent import run_seo_agent
from peacock_agents.technical_seo_agent import run_technical_seo_agent

AGENT_REGISTRY = {
    "seo_agent": run_seo_agent,
    "aeo_agent": run_aeo_agent,
    "geo_agent": run_geo_agent,
    "research_agent": run_research_agent,
    "content_strategist_agent": run_content_strategist_agent,
    "competitor_agent": run_competitor_agent,
    "citation_agent": run_citation_agent,
    "internal_linking_agent": run_internal_linking_agent,
    "technical_seo_agent": run_technical_seo_agent,
    "content_refresh_agent": run_content_refresh_agent,
    "measurement_agent": run_measurement_agent,
    "experiment_agent": run_experiment_agent,
}

__all__ = [
    "AGENT_GUARDRAIL_NOTE",
    "AGENT_REGISTRY",
    "AgentDraft",
    "AgentResult",
    "AgentTask",
    "run_aeo_agent",
    "run_citation_agent",
    "run_competitor_agent",
    "run_content_refresh_agent",
    "run_content_strategist_agent",
    "run_experiment_agent",
    "run_geo_agent",
    "run_internal_linking_agent",
    "run_measurement_agent",
    "run_research_agent",
    "run_seo_agent",
    "run_technical_seo_agent",
]
