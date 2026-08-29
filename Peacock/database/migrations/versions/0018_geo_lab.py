"""Peacock GEO Lab — controlled generative-engine experimentation

Revision ID: 0018_geo_lab
Revises: 0017_content_digital_twin
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0018_geo_lab"
down_revision: Union[str, None] = "0017_content_digital_twin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "geo_lab_experiments",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("topic_cluster", sa.String(length=255), nullable=True),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("experiment_status", sa.String(length=32), nullable=False),
        sa.Column("design_type", sa.String(length=64), nullable=False),
        sa.Column("pre_window_start", sa.String(length=32), nullable=True),
        sa.Column("pre_window_end", sa.String(length=32), nullable=True),
        sa.Column("post_window_start", sa.String(length=32), nullable=True),
        sa.Column("post_window_end", sa.String(length=32), nullable=True),
        sa.Column("intervention_date", sa.String(length=32), nullable=True),
        sa.Column("has_control_pages", sa.Boolean(), nullable=False),
        sa.Column("has_matched_groups", sa.Boolean(), nullable=False),
        sa.Column("has_time_series", sa.Boolean(), nullable=False),
        sa.Column("causality_warning", sa.Text(), nullable=False),
        sa.Column("overall_causality_level", sa.String(length=32), nullable=False),
        sa.Column("overall_summary", sa.Text(), nullable=True),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_geo_lab_experiments_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_geo_lab_experiments_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_geo_lab_experiments_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_geo_lab_experiments_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_geo_lab_experiments")),
    )
    op.create_index(op.f("ix_geo_lab_experiments_website_id"), "geo_lab_experiments", ["website_id"], unique=False)
    op.create_index(op.f("ix_geo_lab_experiments_client_brand"), "geo_lab_experiments", ["client_brand"], unique=False)
    op.create_index(op.f("ix_geo_lab_experiments_topic_cluster"), "geo_lab_experiments", ["topic_cluster"], unique=False)
    op.create_index(op.f("ix_geo_lab_experiments_experiment_status"), "geo_lab_experiments", ["experiment_status"], unique=False)
    op.create_index(op.f("ix_geo_lab_experiments_design_type"), "geo_lab_experiments", ["design_type"], unique=False)
    op.create_index(op.f("ix_geo_lab_experiments_intervention_date"), "geo_lab_experiments", ["intervention_date"], unique=False)
    op.create_index(op.f("ix_geo_lab_experiments_overall_causality_level"), "geo_lab_experiments", ["overall_causality_level"], unique=False)
    op.create_index(op.f("ix_geo_lab_experiments_organisation_id"), "geo_lab_experiments", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_geo_lab_experiments_workspace_id"), "geo_lab_experiments", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_geo_lab_experiments_created_by"), "geo_lab_experiments", ["created_by"], unique=False)
    op.create_index(op.f("ix_geo_lab_experiments_status"), "geo_lab_experiments", ["status"], unique=False)

    op.create_table(
        "gl_variants",
        sa.Column("experiment_id", sa.String(length=36), nullable=False),
        sa.Column("variant_code", sa.String(length=16), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("treatment_description", sa.Text(), nullable=False),
        sa.Column("is_baseline", sa.Boolean(), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_gl_variants_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["experiment_id"], ["geo_lab_experiments.id"], name=op.f("fk_gl_variants_experiment_id_geo_lab_experiments"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_gl_variants_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_gl_variants_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_gl_variants")),
        sa.UniqueConstraint("experiment_id", "variant_code", name=op.f("uq_gl_variants_experiment_id")),
    )
    op.create_index(op.f("ix_gl_variants_experiment_id"), "gl_variants", ["experiment_id"], unique=False)
    op.create_index(op.f("ix_gl_variants_variant_code"), "gl_variants", ["variant_code"], unique=False)
    op.create_index(op.f("ix_gl_variants_organisation_id"), "gl_variants", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_gl_variants_workspace_id"), "gl_variants", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_gl_variants_created_by"), "gl_variants", ["created_by"], unique=False)
    op.create_index(op.f("ix_gl_variants_status"), "gl_variants", ["status"], unique=False)

    op.create_table(
        "gl_pages",
        sa.Column("experiment_id", sa.String(length=36), nullable=False),
        sa.Column("variant_id", sa.String(length=36), nullable=True),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("page_role", sa.String(length=16), nullable=False),
        sa.Column("matched_group", sa.String(length=64), nullable=True),
        sa.Column("match_key", sa.String(length=255), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_gl_pages_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["experiment_id"], ["geo_lab_experiments.id"], name=op.f("fk_gl_pages_experiment_id_geo_lab_experiments"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_gl_pages_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["gl_variants.id"], name=op.f("fk_gl_pages_variant_id_gl_variants"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_gl_pages_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_gl_pages")),
        sa.UniqueConstraint("experiment_id", "url", name=op.f("uq_gl_pages_experiment_id")),
    )
    op.create_index(op.f("ix_gl_pages_experiment_id"), "gl_pages", ["experiment_id"], unique=False)
    op.create_index(op.f("ix_gl_pages_variant_id"), "gl_pages", ["variant_id"], unique=False)
    op.create_index(op.f("ix_gl_pages_page_role"), "gl_pages", ["page_role"], unique=False)
    op.create_index(op.f("ix_gl_pages_matched_group"), "gl_pages", ["matched_group"], unique=False)
    op.create_index(op.f("ix_gl_pages_organisation_id"), "gl_pages", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_gl_pages_workspace_id"), "gl_pages", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_gl_pages_created_by"), "gl_pages", ["created_by"], unique=False)
    op.create_index(op.f("ix_gl_pages_status"), "gl_pages", ["status"], unique=False)

    op.create_table(
        "gl_metric_observations",
        sa.Column("experiment_id", sa.String(length=36), nullable=False),
        sa.Column("page_id", sa.String(length=36), nullable=False),
        sa.Column("metric_code", sa.String(length=64), nullable=False),
        sa.Column("observed_at", sa.String(length=32), nullable=False),
        sa.Column("period", sa.String(length=16), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("engine", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_gl_metric_observations_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["experiment_id"], ["geo_lab_experiments.id"], name=op.f("fk_gl_metric_observations_experiment_id_geo_lab_experiments"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_gl_metric_observations_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["page_id"], ["gl_pages.id"], name=op.f("fk_gl_metric_observations_page_id_gl_pages"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_gl_metric_observations_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_gl_metric_observations")),
        sa.UniqueConstraint("experiment_id", "page_id", "metric_code", "observed_at", name=op.f("uq_gl_metric_observations_experiment_id")),
    )
    op.create_index(op.f("ix_gl_metric_observations_experiment_id"), "gl_metric_observations", ["experiment_id"], unique=False)
    op.create_index(op.f("ix_gl_metric_observations_page_id"), "gl_metric_observations", ["page_id"], unique=False)
    op.create_index(op.f("ix_gl_metric_observations_metric_code"), "gl_metric_observations", ["metric_code"], unique=False)
    op.create_index(op.f("ix_gl_metric_observations_observed_at"), "gl_metric_observations", ["observed_at"], unique=False)
    op.create_index(op.f("ix_gl_metric_observations_period"), "gl_metric_observations", ["period"], unique=False)
    op.create_index(op.f("ix_gl_metric_observations_engine"), "gl_metric_observations", ["engine"], unique=False)
    op.create_index(op.f("ix_gl_metric_observations_organisation_id"), "gl_metric_observations", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_gl_metric_observations_workspace_id"), "gl_metric_observations", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_gl_metric_observations_created_by"), "gl_metric_observations", ["created_by"], unique=False)
    op.create_index(op.f("ix_gl_metric_observations_status"), "gl_metric_observations", ["status"], unique=False)

    op.create_table(
        "gl_metric_deltas",
        sa.Column("experiment_id", sa.String(length=36), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.Column("metric_code", sa.String(length=64), nullable=False),
        sa.Column("pre_mean", sa.Float(), nullable=False),
        sa.Column("post_mean", sa.Float(), nullable=False),
        sa.Column("absolute_delta", sa.Float(), nullable=False),
        sa.Column("relative_delta_pct", sa.Float(), nullable=True),
        sa.Column("control_adjusted_delta", sa.Float(), nullable=True),
        sa.Column("observation_count_pre", sa.Integer(), nullable=False),
        sa.Column("observation_count_post", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_gl_metric_deltas_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["experiment_id"], ["geo_lab_experiments.id"], name=op.f("fk_gl_metric_deltas_experiment_id_geo_lab_experiments"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_gl_metric_deltas_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_gl_metric_deltas_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_gl_metric_deltas")),
        sa.UniqueConstraint("experiment_id", "scope_type", "scope_id", "metric_code", name=op.f("uq_gl_metric_deltas_experiment_id")),
    )
    op.create_index(op.f("ix_gl_metric_deltas_experiment_id"), "gl_metric_deltas", ["experiment_id"], unique=False)
    op.create_index(op.f("ix_gl_metric_deltas_scope_type"), "gl_metric_deltas", ["scope_type"], unique=False)
    op.create_index(op.f("ix_gl_metric_deltas_scope_id"), "gl_metric_deltas", ["scope_id"], unique=False)
    op.create_index(op.f("ix_gl_metric_deltas_metric_code"), "gl_metric_deltas", ["metric_code"], unique=False)
    op.create_index(op.f("ix_gl_metric_deltas_organisation_id"), "gl_metric_deltas", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_gl_metric_deltas_workspace_id"), "gl_metric_deltas", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_gl_metric_deltas_created_by"), "gl_metric_deltas", ["created_by"], unique=False)
    op.create_index(op.f("ix_gl_metric_deltas_status"), "gl_metric_deltas", ["status"], unique=False)

    op.create_table(
        "gl_causality_assessments",
        sa.Column("experiment_id", sa.String(length=36), nullable=False),
        sa.Column("metric_code", sa.String(length=64), nullable=False),
        sa.Column("variant_code", sa.String(length=16), nullable=False),
        sa.Column("causality_level", sa.String(length=32), nullable=False),
        sa.Column("claim_allowed", sa.Boolean(), nullable=False),
        sa.Column("auto_causal_conclusion_rejected", sa.Boolean(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("confounds_noted", sa.Text(), nullable=True),
        sa.Column("design_supports", sa.Text(), nullable=False),
        sa.Column("confidence_note", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_gl_causality_assessments_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["experiment_id"], ["geo_lab_experiments.id"], name=op.f("fk_gl_causality_assessments_experiment_id_geo_lab_experiments"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_gl_causality_assessments_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_gl_causality_assessments_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_gl_causality_assessments")),
        sa.UniqueConstraint("experiment_id", "metric_code", "variant_code", name=op.f("uq_gl_causality_assessments_experiment_id")),
    )
    op.create_index(op.f("ix_gl_causality_assessments_experiment_id"), "gl_causality_assessments", ["experiment_id"], unique=False)
    op.create_index(op.f("ix_gl_causality_assessments_metric_code"), "gl_causality_assessments", ["metric_code"], unique=False)
    op.create_index(op.f("ix_gl_causality_assessments_variant_code"), "gl_causality_assessments", ["variant_code"], unique=False)
    op.create_index(op.f("ix_gl_causality_assessments_causality_level"), "gl_causality_assessments", ["causality_level"], unique=False)
    op.create_index(op.f("ix_gl_causality_assessments_organisation_id"), "gl_causality_assessments", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_gl_causality_assessments_workspace_id"), "gl_causality_assessments", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_gl_causality_assessments_created_by"), "gl_causality_assessments", ["created_by"], unique=False)
    op.create_index(op.f("ix_gl_causality_assessments_status"), "gl_causality_assessments", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("gl_causality_assessments")
    op.drop_table("gl_metric_deltas")
    op.drop_table("gl_metric_observations")
    op.drop_table("gl_pages")
    op.drop_table("gl_variants")
    op.drop_table("geo_lab_experiments")
