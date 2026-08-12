"""Peacock Citation Graph — pathways, CIS, source opportunities

Revision ID: 0012_citation_graph
Revises: 0011_share_of_answer
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0012_citation_graph"
down_revision: Union[str, None] = "0011_share_of_answer"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "citation_graph_analyses",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("topic_cluster", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("analysis_status", sa.String(length=32), nullable=False),
        sa.Column("observation_count", sa.Integer(), nullable=False),
        sa.Column("citation_count", sa.Integer(), nullable=False),
        sa.Column("domain_count", sa.Integer(), nullable=False),
        sa.Column("pathway_count", sa.Integer(), nullable=False),
        sa.Column("opportunity_count", sa.Integer(), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_citation_graph_analyses_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_citation_graph_analyses_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_citation_graph_analyses_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_citation_graph_analyses_organisation_id_organisations"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_citation_graph_analyses")),
    )
    op.create_index(op.f("ix_citation_graph_analyses_organisation_id"), "citation_graph_analyses", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_citation_graph_analyses_website_id"), "citation_graph_analyses", ["website_id"], unique=False)
    op.create_index(op.f("ix_citation_graph_analyses_status"), "citation_graph_analyses", ["status"], unique=False)
    op.create_index(op.f("ix_citation_graph_analyses_topic_cluster"), "citation_graph_analyses", ["topic_cluster"], unique=False)
    op.create_index(op.f("ix_citation_graph_analyses_analysis_status"), "citation_graph_analyses", ["analysis_status"], unique=False)
    op.create_index(op.f("ix_citation_graph_analyses_created_by"), "citation_graph_analyses", ["created_by"], unique=False)
    op.create_index(op.f("ix_citation_graph_analyses_client_brand"), "citation_graph_analyses", ["client_brand"], unique=False)
    op.create_index(op.f("ix_citation_graph_analyses_workspace_id"), "citation_graph_analyses", ["workspace_id"], unique=False)

    op.create_table(
        "cg_observations",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("engine_code", sa.String(length=64), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("answer_excerpt", sa.Text(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_code", sa.String(length=128), nullable=True),
        sa.Column("topic_label", sa.String(length=255), nullable=True),
        sa.Column("visibility_probe_observation_id", sa.String(length=36), nullable=True),
        sa.Column("ai_query_run_id", sa.String(length=36), nullable=True),
        sa.Column("citation_observation_id", sa.String(length=36), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_cg_observations_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["visibility_probe_observation_id"], ["visibility_probe_observations.id"], name=op.f("fk_cg_observations_visibility_probe_observation_id_visibility_probe_observations"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ai_query_run_id"], ["ai_query_runs.id"], name=op.f("fk_cg_observations_ai_query_run_id_ai_query_runs"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["analysis_id"], ["citation_graph_analyses.id"], name=op.f("fk_cg_observations_analysis_id_citation_graph_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_cg_observations_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["citation_observation_id"], ["citation_observations.id"], name=op.f("fk_cg_observations_citation_observation_id_citation_observations"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_cg_observations_created_by_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cg_observations")),
    )
    op.create_index(op.f("ix_cg_observations_organisation_id"), "cg_observations", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_cg_observations_visibility_probe_observation_id"), "cg_observations", ["visibility_probe_observation_id"], unique=False)
    op.create_index(op.f("ix_cg_observations_status"), "cg_observations", ["status"], unique=False)
    op.create_index(op.f("ix_cg_observations_observed_at"), "cg_observations", ["observed_at"], unique=False)
    op.create_index(op.f("ix_cg_observations_engine_code"), "cg_observations", ["engine_code"], unique=False)
    op.create_index(op.f("ix_cg_observations_created_by"), "cg_observations", ["created_by"], unique=False)
    op.create_index(op.f("ix_cg_observations_topic_label"), "cg_observations", ["topic_label"], unique=False)
    op.create_index(op.f("ix_cg_observations_citation_observation_id"), "cg_observations", ["citation_observation_id"], unique=False)
    op.create_index(op.f("ix_cg_observations_analysis_id"), "cg_observations", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_cg_observations_workspace_id"), "cg_observations", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_cg_observations_ai_query_run_id"), "cg_observations", ["ai_query_run_id"], unique=False)

    op.create_table(
        "cg_citations",
        sa.Column("observation_id", sa.String(length=36), nullable=False),
        sa.Column("cited_url", sa.String(length=2048), nullable=False),
        sa.Column("cited_domain", sa.String(length=255), nullable=False),
        sa.Column("page_path", sa.String(length=2048), nullable=True),
        sa.Column("source_class", sa.String(length=64), nullable=False),
        sa.Column("is_competitor_owned", sa.Boolean(), nullable=False),
        sa.Column("is_client_owned", sa.Boolean(), nullable=False),
        sa.Column("prominence", sa.Float(), nullable=False),
        sa.Column("freshness_days", sa.Integer(), nullable=True),
        sa.Column("authority_proxy", sa.Float(), nullable=False),
        sa.Column("position_in_answer", sa.Integer(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_cg_citations_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_cg_citations_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["observation_id"], ["cg_observations.id"], name=op.f("fk_cg_citations_observation_id_cg_observations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_cg_citations_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cg_citations")),
    )
    op.create_index(op.f("ix_cg_citations_cited_domain"), "cg_citations", ["cited_domain"], unique=False)
    op.create_index(op.f("ix_cg_citations_status"), "cg_citations", ["status"], unique=False)
    op.create_index(op.f("ix_cg_citations_created_by"), "cg_citations", ["created_by"], unique=False)
    op.create_index(op.f("ix_cg_citations_workspace_id"), "cg_citations", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_cg_citations_source_class"), "cg_citations", ["source_class"], unique=False)
    op.create_index(op.f("ix_cg_citations_observation_id"), "cg_citations", ["observation_id"], unique=False)
    op.create_index(op.f("ix_cg_citations_organisation_id"), "cg_citations", ["organisation_id"], unique=False)

    op.create_table(
        "cg_entity_mentions",
        sa.Column("observation_id", sa.String(length=36), nullable=False),
        sa.Column("entity_name", sa.String(length=255), nullable=False),
        sa.Column("is_client", sa.Boolean(), nullable=False),
        sa.Column("is_competitor", sa.Boolean(), nullable=False),
        sa.Column("mentioned", sa.Boolean(), nullable=False),
        sa.Column("position_hint", sa.Integer(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_cg_entity_mentions_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_cg_entity_mentions_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["observation_id"], ["cg_observations.id"], name=op.f("fk_cg_entity_mentions_observation_id_cg_observations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_cg_entity_mentions_created_by_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cg_entity_mentions")),
    )
    op.create_index(op.f("ix_cg_entity_mentions_organisation_id"), "cg_entity_mentions", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_cg_entity_mentions_is_client"), "cg_entity_mentions", ["is_client"], unique=False)
    op.create_index(op.f("ix_cg_entity_mentions_status"), "cg_entity_mentions", ["status"], unique=False)
    op.create_index(op.f("ix_cg_entity_mentions_created_by"), "cg_entity_mentions", ["created_by"], unique=False)
    op.create_index(op.f("ix_cg_entity_mentions_observation_id"), "cg_entity_mentions", ["observation_id"], unique=False)
    op.create_index(op.f("ix_cg_entity_mentions_workspace_id"), "cg_entity_mentions", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_cg_entity_mentions_entity_name"), "cg_entity_mentions", ["entity_name"], unique=False)

    op.create_table(
        "cg_pathways",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("observation_id", sa.String(length=36), nullable=False),
        sa.Column("citation_id", sa.String(length=36), nullable=False),
        sa.Column("engine_code", sa.String(length=64), nullable=False),
        sa.Column("prompt_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("answer_id", sa.String(length=36), nullable=False),
        sa.Column("cited_url", sa.String(length=2048), nullable=False),
        sa.Column("cited_domain", sa.String(length=255), nullable=False),
        sa.Column("page_path", sa.String(length=2048), nullable=True),
        sa.Column("entity_name", sa.String(length=255), nullable=True),
        sa.Column("topic_label", sa.String(length=255), nullable=False),
        sa.Column("source_class", sa.String(length=64), nullable=False),
        sa.Column("pathway_key", sa.String(length=128), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["citation_graph_analyses.id"], name=op.f("fk_cg_pathways_analysis_id_citation_graph_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_cg_pathways_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["observation_id"], ["cg_observations.id"], name=op.f("fk_cg_pathways_observation_id_cg_observations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_cg_pathways_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_cg_pathways_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["citation_id"], ["cg_citations.id"], name=op.f("fk_cg_pathways_citation_id_cg_citations"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cg_pathways")),
    )
    op.create_index(op.f("ix_cg_pathways_analysis_id"), "cg_pathways", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_cg_pathways_pathway_key"), "cg_pathways", ["pathway_key"], unique=False)
    op.create_index(op.f("ix_cg_pathways_prompt_fingerprint"), "cg_pathways", ["prompt_fingerprint"], unique=False)
    op.create_index(op.f("ix_cg_pathways_engine_code"), "cg_pathways", ["engine_code"], unique=False)
    op.create_index(op.f("ix_cg_pathways_workspace_id"), "cg_pathways", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_cg_pathways_entity_name"), "cg_pathways", ["entity_name"], unique=False)
    op.create_index(op.f("ix_cg_pathways_topic_label"), "cg_pathways", ["topic_label"], unique=False)
    op.create_index(op.f("ix_cg_pathways_answer_id"), "cg_pathways", ["answer_id"], unique=False)
    op.create_index(op.f("ix_cg_pathways_cited_domain"), "cg_pathways", ["cited_domain"], unique=False)
    op.create_index(op.f("ix_cg_pathways_organisation_id"), "cg_pathways", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_cg_pathways_status"), "cg_pathways", ["status"], unique=False)
    op.create_index(op.f("ix_cg_pathways_created_by"), "cg_pathways", ["created_by"], unique=False)
    op.create_index(op.f("ix_cg_pathways_source_class"), "cg_pathways", ["source_class"], unique=False)
    op.create_index(op.f("ix_cg_pathways_observation_id"), "cg_pathways", ["observation_id"], unique=False)
    op.create_index(op.f("ix_cg_pathways_citation_id"), "cg_pathways", ["citation_id"], unique=False)

    op.create_table(
        "cg_domain_scores",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("cited_domain", sa.String(length=255), nullable=False),
        sa.Column("source_class", sa.String(length=64), nullable=False),
        sa.Column("is_citation_hub", sa.Boolean(), nullable=False),
        sa.Column("is_competitor_owned", sa.Boolean(), nullable=False),
        sa.Column("is_client_owned", sa.Boolean(), nullable=False),
        sa.Column("citation_influence_score", sa.Float(), nullable=False),
        sa.Column("citation_frequency", sa.Float(), nullable=False),
        sa.Column("cross_engine_citation", sa.Float(), nullable=False),
        sa.Column("topic_coverage", sa.Float(), nullable=False),
        sa.Column("prominence", sa.Float(), nullable=False),
        sa.Column("freshness", sa.Float(), nullable=False),
        sa.Column("authority_proxy", sa.Float(), nullable=False),
        sa.Column("brand_association", sa.Float(), nullable=False),
        sa.Column("citation_diversity", sa.Float(), nullable=False),
        sa.Column("citation_count", sa.Integer(), nullable=False),
        sa.Column("engine_count", sa.Integer(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("observation_share", sa.Float(), nullable=False),
        sa.Column("client_mention_rate", sa.Float(), nullable=False),
        sa.Column("competitor_mention_rate", sa.Float(), nullable=False),
        sa.Column("component_explanations", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_cg_domain_scores_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_cg_domain_scores_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["analysis_id"], ["citation_graph_analyses.id"], name=op.f("fk_cg_domain_scores_analysis_id_citation_graph_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_cg_domain_scores_organisation_id_organisations"), ondelete="CASCADE"),
        sa.UniqueConstraint("analysis_id", "cited_domain", name=op.f("uq_cg_domain_scores_analysis_id_cited_domain")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cg_domain_scores")),
    )
    op.create_index(op.f("ix_cg_domain_scores_source_class"), "cg_domain_scores", ["source_class"], unique=False)
    op.create_index(op.f("ix_cg_domain_scores_status"), "cg_domain_scores", ["status"], unique=False)
    op.create_index(op.f("ix_cg_domain_scores_created_by"), "cg_domain_scores", ["created_by"], unique=False)
    op.create_index(op.f("ix_cg_domain_scores_cited_domain"), "cg_domain_scores", ["cited_domain"], unique=False)
    op.create_index(op.f("ix_cg_domain_scores_is_citation_hub"), "cg_domain_scores", ["is_citation_hub"], unique=False)
    op.create_index(op.f("ix_cg_domain_scores_analysis_id"), "cg_domain_scores", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_cg_domain_scores_workspace_id"), "cg_domain_scores", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_cg_domain_scores_organisation_id"), "cg_domain_scores", ["organisation_id"], unique=False)

    op.create_table(
        "cg_source_opportunities",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("cited_domain", sa.String(length=255), nullable=False),
        sa.Column("source_class", sa.String(length=64), nullable=False),
        sa.Column("opportunity_type", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("domain_answer_influence_pct", sa.Float(), nullable=False),
        sa.Column("client_mention_pct", sa.Float(), nullable=False),
        sa.Column("top_competitor_name", sa.String(length=255), nullable=True),
        sa.Column("top_competitor_mention_pct", sa.Float(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("recommended_actions", sa.Text(), nullable=False),
        sa.Column("manipulative_spam_rejected", sa.Boolean(), nullable=False),
        sa.Column("forbidden_tactics_note", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_cg_source_opportunities_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_cg_source_opportunities_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_id"], ["citation_graph_analyses.id"], name=op.f("fk_cg_source_opportunities_analysis_id_citation_graph_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_cg_source_opportunities_created_by_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cg_source_opportunities")),
    )
    op.create_index(op.f("ix_cg_source_opportunities_created_by"), "cg_source_opportunities", ["created_by"], unique=False)
    op.create_index(op.f("ix_cg_source_opportunities_analysis_id"), "cg_source_opportunities", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_cg_source_opportunities_organisation_id"), "cg_source_opportunities", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_cg_source_opportunities_priority"), "cg_source_opportunities", ["priority"], unique=False)
    op.create_index(op.f("ix_cg_source_opportunities_cited_domain"), "cg_source_opportunities", ["cited_domain"], unique=False)
    op.create_index(op.f("ix_cg_source_opportunities_workspace_id"), "cg_source_opportunities", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_cg_source_opportunities_source_class"), "cg_source_opportunities", ["source_class"], unique=False)
    op.create_index(op.f("ix_cg_source_opportunities_opportunity_type"), "cg_source_opportunities", ["opportunity_type"], unique=False)
    op.create_index(op.f("ix_cg_source_opportunities_status"), "cg_source_opportunities", ["status"], unique=False)



def downgrade() -> None:

    op.drop_table("cg_source_opportunities")
    op.drop_table("cg_domain_scores")
    op.drop_table("cg_pathways")
    op.drop_table("cg_entity_mentions")
    op.drop_table("cg_citations")
    op.drop_table("cg_observations")
    op.drop_table("citation_graph_analyses")

