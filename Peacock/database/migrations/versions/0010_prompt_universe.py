"""Prompt Universe Intelligence — full intent landscape

Revision ID: 0010_prompt_universe
Revises: 0009_probabilistic_visibility
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_prompt_universe"
down_revision: Union[str, None] = "0009_probabilistic_visibility"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prompt_universes",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("brand_name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=128), nullable=True),
        sa.Column("primary_location", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("generation_status", sa.String(length=32), nullable=False),
        sa.Column("prompt_count", sa.Integer(), nullable=False),
        sa.Column("family_count", sa.Integer(), nullable=False),
        sa.Column("signal_count", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_prompt_universes_created_by_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_prompt_universes_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["website_id"], ["websites.id"], name=op.f("fk_prompt_universes_website_id_websites"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_prompt_universes_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prompt_universes")),
    )
    op.create_index(op.f("ix_prompt_universes_brand_name"), "prompt_universes", ["brand_name"], unique=False)
    op.create_index(op.f("ix_prompt_universes_created_by"), "prompt_universes", ["created_by"], unique=False)
    op.create_index(
        op.f("ix_prompt_universes_generation_status"), "prompt_universes", ["generation_status"], unique=False
    )
    op.create_index(
        op.f("ix_prompt_universes_organisation_id"), "prompt_universes", ["organisation_id"], unique=False
    )
    op.create_index(op.f("ix_prompt_universes_status"), "prompt_universes", ["status"], unique=False)
    op.create_index(op.f("ix_prompt_universes_website_id"), "prompt_universes", ["website_id"], unique=False)
    op.create_index(op.f("ix_prompt_universes_workspace_id"), "prompt_universes", ["workspace_id"], unique=False)

    op.create_table(
        "synthetic_personas",
        sa.Column("universe_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("query_style", sa.String(length=64), nullable=False),
        sa.Column("is_system_seed", sa.Boolean(), nullable=False),
        sa.Column("context_template", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_synthetic_personas_created_by_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_synthetic_personas_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["universe_id"],
            ["prompt_universes.id"],
            name=op.f("fk_synthetic_personas_universe_id_prompt_universes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_synthetic_personas_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_synthetic_personas")),
        sa.UniqueConstraint("universe_id", "code", name=op.f("uq_synthetic_personas_universe_id")),
    )
    op.create_index(op.f("ix_synthetic_personas_code"), "synthetic_personas", ["code"], unique=False)
    op.create_index(op.f("ix_synthetic_personas_created_by"), "synthetic_personas", ["created_by"], unique=False)
    op.create_index(
        op.f("ix_synthetic_personas_organisation_id"), "synthetic_personas", ["organisation_id"], unique=False
    )
    op.create_index(op.f("ix_synthetic_personas_status"), "synthetic_personas", ["status"], unique=False)
    op.create_index(op.f("ix_synthetic_personas_universe_id"), "synthetic_personas", ["universe_id"], unique=False)
    op.create_index(op.f("ix_synthetic_personas_workspace_id"), "synthetic_personas", ["workspace_id"], unique=False)

    op.create_table(
        "prompt_source_signals",
        sa.Column("universe_id", sa.String(length=36), nullable=False),
        sa.Column("source_kind", sa.String(length=64), nullable=False),
        sa.Column("signal_text", sa.Text(), nullable=False),
        sa.Column("signal_key", sa.String(length=255), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("location_code", sa.String(length=64), nullable=True),
        sa.Column("product_name", sa.String(length=255), nullable=True),
        sa.Column("topic_hint", sa.String(length=255), nullable=True),
        sa.Column("external_ref", sa.String(length=512), nullable=True),
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
            name=op.f("fk_prompt_source_signals_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_prompt_source_signals_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["universe_id"],
            ["prompt_universes.id"],
            name=op.f("fk_prompt_source_signals_universe_id_prompt_universes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_prompt_source_signals_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prompt_source_signals")),
    )
    op.create_index(
        op.f("ix_prompt_source_signals_created_by"), "prompt_source_signals", ["created_by"], unique=False
    )
    op.create_index(
        op.f("ix_prompt_source_signals_organisation_id"),
        "prompt_source_signals",
        ["organisation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prompt_source_signals_signal_key"), "prompt_source_signals", ["signal_key"], unique=False
    )
    op.create_index(
        op.f("ix_prompt_source_signals_source_kind"), "prompt_source_signals", ["source_kind"], unique=False
    )
    op.create_index(op.f("ix_prompt_source_signals_status"), "prompt_source_signals", ["status"], unique=False)
    op.create_index(
        op.f("ix_prompt_source_signals_universe_id"), "prompt_source_signals", ["universe_id"], unique=False
    )
    op.create_index(
        op.f("ix_prompt_source_signals_workspace_id"), "prompt_source_signals", ["workspace_id"], unique=False
    )

    op.create_table(
        "prompt_families",
        sa.Column("universe_id", sa.String(length=36), nullable=False),
        sa.Column("seed_signal_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("member_count", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_prompt_families_created_by_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_prompt_families_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["seed_signal_id"],
            ["prompt_source_signals.id"],
            name=op.f("fk_prompt_families_seed_signal_id_prompt_source_signals"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["universe_id"],
            ["prompt_universes.id"],
            name=op.f("fk_prompt_families_universe_id_prompt_universes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_prompt_families_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prompt_families")),
        sa.UniqueConstraint("universe_id", "slug", name=op.f("uq_prompt_families_universe_id")),
    )
    op.create_index(op.f("ix_prompt_families_created_by"), "prompt_families", ["created_by"], unique=False)
    op.create_index(op.f("ix_prompt_families_organisation_id"), "prompt_families", ["organisation_id"], unique=False)
    op.create_index(
        op.f("ix_prompt_families_seed_signal_id"), "prompt_families", ["seed_signal_id"], unique=False
    )
    op.create_index(op.f("ix_prompt_families_status"), "prompt_families", ["status"], unique=False)
    op.create_index(op.f("ix_prompt_families_topic"), "prompt_families", ["topic"], unique=False)
    op.create_index(op.f("ix_prompt_families_universe_id"), "prompt_families", ["universe_id"], unique=False)
    op.create_index(op.f("ix_prompt_families_workspace_id"), "prompt_families", ["workspace_id"], unique=False)

    op.create_table(
        "universe_prompts",
        sa.Column("universe_id", sa.String(length=36), nullable=False),
        sa.Column("family_id", sa.String(length=36), nullable=True),
        sa.Column("persona_id", sa.String(length=36), nullable=True),
        sa.Column("parent_prompt_id", sa.String(length=36), nullable=True),
        sa.Column("ai_query_id", sa.String(length=36), nullable=True),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("prompt_hash", sa.String(length=64), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("subtopic", sa.String(length=255), nullable=True),
        sa.Column("intent", sa.String(length=64), nullable=False),
        sa.Column("persona_code", sa.String(length=64), nullable=False),
        sa.Column("funnel_stage", sa.String(length=32), nullable=False),
        sa.Column("location", sa.String(length=64), nullable=False),
        sa.Column("product", sa.String(length=255), nullable=True),
        sa.Column("problem", sa.Text(), nullable=True),
        sa.Column("commercial_value", sa.Float(), nullable=False),
        sa.Column("brand_relevance", sa.Float(), nullable=False),
        sa.Column("prompt_type", sa.String(length=32), nullable=False),
        sa.Column("source_kind", sa.String(length=64), nullable=False),
        sa.Column("complexity", sa.String(length=32), nullable=False),
        sa.Column("is_tracked", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["ai_query_id"], ["ai_queries.id"], name=op.f("fk_universe_prompts_ai_query_id_ai_queries"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_universe_prompts_created_by_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["family_id"],
            ["prompt_families.id"],
            name=op.f("fk_universe_prompts_family_id_prompt_families"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_universe_prompts_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_prompt_id"],
            ["universe_prompts.id"],
            name=op.f("fk_universe_prompts_parent_prompt_id_universe_prompts"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["persona_id"],
            ["synthetic_personas.id"],
            name=op.f("fk_universe_prompts_persona_id_synthetic_personas"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["universe_id"],
            ["prompt_universes.id"],
            name=op.f("fk_universe_prompts_universe_id_prompt_universes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_universe_prompts_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_universe_prompts")),
        sa.UniqueConstraint(
            "universe_id", "prompt_hash", "persona_code", name=op.f("uq_universe_prompts_universe_id")
        ),
    )
    op.create_index(op.f("ix_universe_prompts_ai_query_id"), "universe_prompts", ["ai_query_id"], unique=False)
    op.create_index(op.f("ix_universe_prompts_complexity"), "universe_prompts", ["complexity"], unique=False)
    op.create_index(op.f("ix_universe_prompts_created_by"), "universe_prompts", ["created_by"], unique=False)
    op.create_index(op.f("ix_universe_prompts_family_id"), "universe_prompts", ["family_id"], unique=False)
    op.create_index(op.f("ix_universe_prompts_funnel_stage"), "universe_prompts", ["funnel_stage"], unique=False)
    op.create_index(op.f("ix_universe_prompts_intent"), "universe_prompts", ["intent"], unique=False)
    op.create_index(op.f("ix_universe_prompts_is_tracked"), "universe_prompts", ["is_tracked"], unique=False)
    op.create_index(op.f("ix_universe_prompts_location"), "universe_prompts", ["location"], unique=False)
    op.create_index(
        op.f("ix_universe_prompts_organisation_id"), "universe_prompts", ["organisation_id"], unique=False
    )
    op.create_index(
        op.f("ix_universe_prompts_parent_prompt_id"), "universe_prompts", ["parent_prompt_id"], unique=False
    )
    op.create_index(op.f("ix_universe_prompts_persona_code"), "universe_prompts", ["persona_code"], unique=False)
    op.create_index(op.f("ix_universe_prompts_persona_id"), "universe_prompts", ["persona_id"], unique=False)
    op.create_index(op.f("ix_universe_prompts_prompt_hash"), "universe_prompts", ["prompt_hash"], unique=False)
    op.create_index(op.f("ix_universe_prompts_prompt_type"), "universe_prompts", ["prompt_type"], unique=False)
    op.create_index(op.f("ix_universe_prompts_source_kind"), "universe_prompts", ["source_kind"], unique=False)
    op.create_index(op.f("ix_universe_prompts_status"), "universe_prompts", ["status"], unique=False)
    op.create_index(op.f("ix_universe_prompts_topic"), "universe_prompts", ["topic"], unique=False)
    op.create_index(op.f("ix_universe_prompts_universe_id"), "universe_prompts", ["universe_id"], unique=False)
    op.create_index(op.f("ix_universe_prompts_workspace_id"), "universe_prompts", ["workspace_id"], unique=False)

    op.create_table(
        "prompt_generation_runs",
        sa.Column("universe_id", sa.String(length=36), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("run_status", sa.String(length=32), nullable=False),
        sa.Column("signals_consumed", sa.Integer(), nullable=False),
        sa.Column("prompts_created", sa.Integer(), nullable=False),
        sa.Column("families_created", sa.Integer(), nullable=False),
        sa.Column("personas_materialised", sa.Integer(), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
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
            name=op.f("fk_prompt_generation_runs_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_prompt_generation_runs_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["universe_id"],
            ["prompt_universes.id"],
            name=op.f("fk_prompt_generation_runs_universe_id_prompt_universes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_prompt_generation_runs_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prompt_generation_runs")),
    )
    op.create_index(
        op.f("ix_prompt_generation_runs_created_by"), "prompt_generation_runs", ["created_by"], unique=False
    )
    op.create_index(
        op.f("ix_prompt_generation_runs_organisation_id"),
        "prompt_generation_runs",
        ["organisation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prompt_generation_runs_run_status"), "prompt_generation_runs", ["run_status"], unique=False
    )
    op.create_index(op.f("ix_prompt_generation_runs_status"), "prompt_generation_runs", ["status"], unique=False)
    op.create_index(
        op.f("ix_prompt_generation_runs_universe_id"), "prompt_generation_runs", ["universe_id"], unique=False
    )
    op.create_index(
        op.f("ix_prompt_generation_runs_workspace_id"), "prompt_generation_runs", ["workspace_id"], unique=False
    )

    op.add_column(
        "visibility_probe_cells",
        sa.Column("universe_prompt_id", sa.String(length=36), nullable=True),
    )
    op.create_index(
        op.f("ix_visibility_probe_cells_universe_prompt_id"),
        "visibility_probe_cells",
        ["universe_prompt_id"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_visibility_probe_cells_universe_prompt_id_universe_prompts"),
        "visibility_probe_cells",
        "universe_prompts",
        ["universe_prompt_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_visibility_probe_cells_universe_prompt_id_universe_prompts"),
        "visibility_probe_cells",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_visibility_probe_cells_universe_prompt_id"), table_name="visibility_probe_cells")
    op.drop_column("visibility_probe_cells", "universe_prompt_id")

    op.drop_table("prompt_generation_runs")
    op.drop_table("universe_prompts")
    op.drop_table("prompt_families")
    op.drop_table("prompt_source_signals")
    op.drop_table("synthetic_personas")
    op.drop_table("prompt_universes")
