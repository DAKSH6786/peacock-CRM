"""Share of Answer — multi-indicator generative influence

Revision ID: 0011_share_of_answer
Revises: 0010_prompt_universe
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0011_share_of_answer"
down_revision: Union[str, None] = "0010_prompt_universe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "share_of_answer_analyses",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("query_cluster", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("analysis_status", sa.String(length=32), nullable=False),
        sa.Column("observation_count", sa.Integer(), nullable=False),
        sa.Column("entity_count", sa.Integer(), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("token_count_alone_rejected", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_share_of_answer_analyses_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_share_of_answer_analyses_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["website_id"],
            ["websites.id"],
            name=op.f("fk_share_of_answer_analyses_website_id_websites"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_share_of_answer_analyses_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_share_of_answer_analyses")),
    )
    op.create_index(
        op.f("ix_share_of_answer_analyses_analysis_status"),
        "share_of_answer_analyses",
        ["analysis_status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_share_of_answer_analyses_client_brand"),
        "share_of_answer_analyses",
        ["client_brand"],
        unique=False,
    )
    op.create_index(
        op.f("ix_share_of_answer_analyses_created_by"),
        "share_of_answer_analyses",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_share_of_answer_analyses_organisation_id"),
        "share_of_answer_analyses",
        ["organisation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_share_of_answer_analyses_query_cluster"),
        "share_of_answer_analyses",
        ["query_cluster"],
        unique=False,
    )
    op.create_index(
        op.f("ix_share_of_answer_analyses_status"),
        "share_of_answer_analyses",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_share_of_answer_analyses_website_id"),
        "share_of_answer_analyses",
        ["website_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_share_of_answer_analyses_workspace_id"),
        "share_of_answer_analyses",
        ["workspace_id"],
        unique=False,
    )

    op.create_table(
        "soa_answer_observations",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("engine_code", sa.String(length=64), nullable=False),
        sa.Column("model_code", sa.String(length=128), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_excerpt", sa.Text(), nullable=True),
        sa.Column("structured_summary", sa.Text(), nullable=True),
        sa.Column("answer_token_count", sa.Integer(), nullable=True),
        sa.Column("visibility_probe_observation_id", sa.String(length=36), nullable=True),
        sa.Column("ai_query_run_id", sa.String(length=36), nullable=True),
        sa.Column("probe_source", sa.String(length=32), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["ai_query_run_id"],
            ["ai_query_runs.id"],
            name=op.f("fk_soa_answer_observations_ai_query_run_id_ai_query_runs"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["share_of_answer_analyses.id"],
            name=op.f("fk_soa_answer_observations_analysis_id_share_of_answer_analyses"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_soa_answer_observations_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_soa_answer_observations_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["visibility_probe_observation_id"],
            ["visibility_probe_observations.id"],
            name=op.f(
                "fk_soa_answer_observations_visibility_probe_observation_id_visibility_probe_observations"
            ),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_soa_answer_observations_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_soa_answer_observations")),
    )
    op.create_index(
        op.f("ix_soa_answer_observations_ai_query_run_id"),
        "soa_answer_observations",
        ["ai_query_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soa_answer_observations_analysis_id"),
        "soa_answer_observations",
        ["analysis_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soa_answer_observations_created_by"),
        "soa_answer_observations",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soa_answer_observations_engine_code"),
        "soa_answer_observations",
        ["engine_code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soa_answer_observations_observed_at"),
        "soa_answer_observations",
        ["observed_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soa_answer_observations_organisation_id"),
        "soa_answer_observations",
        ["organisation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soa_answer_observations_status"),
        "soa_answer_observations",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soa_answer_observations_visibility_probe_observation_id"),
        "soa_answer_observations",
        ["visibility_probe_observation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soa_answer_observations_workspace_id"),
        "soa_answer_observations",
        ["workspace_id"],
        unique=False,
    )

    op.create_table(
        "soa_entity_indicators",
        sa.Column("observation_id", sa.String(length=36), nullable=False),
        sa.Column("entity_name", sa.String(length=255), nullable=False),
        sa.Column("is_client", sa.Boolean(), nullable=False),
        sa.Column("mention", sa.Boolean(), nullable=False),
        sa.Column("mention_count", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("recommendation_strength", sa.Float(), nullable=False),
        sa.Column("answer_space", sa.Float(), nullable=False),
        sa.Column("citation_ownership", sa.Float(), nullable=False),
        sa.Column("semantic_prominence", sa.Float(), nullable=False),
        sa.Column("positive_claims", sa.Integer(), nullable=False),
        sa.Column("negative_claims", sa.Integer(), nullable=False),
        sa.Column("neutral_claims", sa.Integer(), nullable=False),
        sa.Column("comparison_outcome", sa.String(length=16), nullable=False),
        sa.Column("token_span_ratio", sa.Float(), nullable=False),
        sa.Column("influence_score", sa.Float(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_soa_entity_indicators_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["observation_id"],
            ["soa_answer_observations.id"],
            name=op.f("fk_soa_entity_indicators_observation_id_soa_answer_observations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_soa_entity_indicators_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_soa_entity_indicators_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_soa_entity_indicators")),
        sa.UniqueConstraint(
            "observation_id", "entity_name", name=op.f("uq_soa_entity_indicators_observation_id")
        ),
    )
    op.create_index(
        op.f("ix_soa_entity_indicators_comparison_outcome"),
        "soa_entity_indicators",
        ["comparison_outcome"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soa_entity_indicators_created_by"),
        "soa_entity_indicators",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soa_entity_indicators_entity_name"),
        "soa_entity_indicators",
        ["entity_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soa_entity_indicators_is_client"),
        "soa_entity_indicators",
        ["is_client"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soa_entity_indicators_observation_id"),
        "soa_entity_indicators",
        ["observation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soa_entity_indicators_organisation_id"),
        "soa_entity_indicators",
        ["organisation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soa_entity_indicators_status"),
        "soa_entity_indicators",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soa_entity_indicators_workspace_id"),
        "soa_entity_indicators",
        ["workspace_id"],
        unique=False,
    )

    op.create_table(
        "soa_brand_scores",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("entity_name", sa.String(length=255), nullable=False),
        sa.Column("is_client", sa.Boolean(), nullable=False),
        sa.Column("share_of_answer", sa.Float(), nullable=False),
        sa.Column("mention_rate", sa.Float(), nullable=False),
        sa.Column("avg_position_score", sa.Float(), nullable=False),
        sa.Column("avg_recommendation_strength", sa.Float(), nullable=False),
        sa.Column("avg_answer_space", sa.Float(), nullable=False),
        sa.Column("avg_citation_ownership", sa.Float(), nullable=False),
        sa.Column("avg_semantic_prominence", sa.Float(), nullable=False),
        sa.Column("avg_claim_balance", sa.Float(), nullable=False),
        sa.Column("avg_comparison_score", sa.Float(), nullable=False),
        sa.Column("avg_token_span_ratio", sa.Float(), nullable=False),
        sa.Column("token_only_share", sa.Float(), nullable=False),
        sa.Column("token_vs_influence_gap", sa.Float(), nullable=False),
        sa.Column("positive_claims_total", sa.Integer(), nullable=False),
        sa.Column("negative_claims_total", sa.Integer(), nullable=False),
        sa.Column("neutral_claims_total", sa.Integer(), nullable=False),
        sa.Column("observation_sample_size", sa.Integer(), nullable=False),
        sa.Column("mean_influence", sa.Float(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["share_of_answer_analyses.id"],
            name=op.f("fk_soa_brand_scores_analysis_id_share_of_answer_analyses"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_soa_brand_scores_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_soa_brand_scores_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_soa_brand_scores_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_soa_brand_scores")),
        sa.UniqueConstraint("analysis_id", "entity_name", name=op.f("uq_soa_brand_scores_analysis_id")),
    )
    op.create_index(
        op.f("ix_soa_brand_scores_analysis_id"), "soa_brand_scores", ["analysis_id"], unique=False
    )
    op.create_index(
        op.f("ix_soa_brand_scores_created_by"), "soa_brand_scores", ["created_by"], unique=False
    )
    op.create_index(
        op.f("ix_soa_brand_scores_entity_name"), "soa_brand_scores", ["entity_name"], unique=False
    )
    op.create_index(
        op.f("ix_soa_brand_scores_is_client"), "soa_brand_scores", ["is_client"], unique=False
    )
    op.create_index(
        op.f("ix_soa_brand_scores_organisation_id"),
        "soa_brand_scores",
        ["organisation_id"],
        unique=False,
    )
    op.create_index(op.f("ix_soa_brand_scores_status"), "soa_brand_scores", ["status"], unique=False)
    op.create_index(
        op.f("ix_soa_brand_scores_workspace_id"), "soa_brand_scores", ["workspace_id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("soa_brand_scores")
    op.drop_table("soa_entity_indicators")
    op.drop_table("soa_answer_observations")
    op.drop_table("share_of_answer_analyses")
