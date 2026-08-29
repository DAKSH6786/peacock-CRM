"""Final Peacock Architecture — system map + product difference standard

Revision ID: 0041_final_architecture
Revises: 0040_quality_bar
Create Date: 2026-08-13
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0041_final_architecture"
down_revision: Union[str, None] = "0040_quality_bar"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def _tenant_cols() -> list:
    return [
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def _tenant_fks(table: str) -> list:
    return [
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f(f"fk_{table}_created_by_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f(f"fk_{table}_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f(f"fk_{table}_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{table}")),
    ]


def upgrade() -> None:
    op.create_table(
        "final_architecture_maps",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("stages_count", sa.Integer(), nullable=False),
        sa.Column("observation_sources_count", sa.Integer(), nullable=False),
        sa.Column("pine_lanes_count", sa.Integer(), nullable=False),
        sa.Column("product_questions_count", sa.Integer(), nullable=False),
        sa.Column("learning_loops_to_pine", sa.Boolean(), nullable=False),
        sa.Column("not_only_visibility", sa.Boolean(), nullable=False),
        sa.Column("product_standard_coverage", sa.Float(), nullable=False),
        sa.Column("architecture_diagram", sa.Text(), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("architecture_positioning", sa.Text(), nullable=False),
        sa.Column("product_standard", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("analysed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["website_id"],
            ["websites.id"],
            name=op.f("fk_final_architecture_maps_website_id_websites"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("final_architecture_maps"),
    )
    _ix(
        "final_architecture_maps",
        [
            "website_id",
            "client_brand",
            "analysed_at",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "fa_pipeline_stages",
        sa.Column("map_id", sa.String(length=36), nullable=False),
        sa.Column("stage_key", sa.String(length=64), nullable=False),
        sa.Column("stage_label", sa.String(length=255), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        sa.Column("next_stage_key", sa.String(length=64), nullable=True),
        sa.Column("loops_to_stage_key", sa.String(length=64), nullable=True),
        sa.Column("detail", sa.Text(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["map_id"],
            ["final_architecture_maps.id"],
            name=op.f("fk_fa_pipeline_stages_map_id_final_architecture_maps"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("fa_pipeline_stages"),
        sa.UniqueConstraint(
            "map_id", "stage_key", name=op.f("uq_fa_pipeline_stages_map_id")
        ),
    )
    _ix(
        "fa_pipeline_stages",
        [
            "map_id",
            "stage_key",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "fa_observation_sources",
        sa.Column("map_id", sa.String(length=36), nullable=False),
        sa.Column("source_key", sa.String(length=64), nullable=False),
        sa.Column("source_label", sa.String(length=255), nullable=False),
        sa.Column("feeds_evidence_ledger", sa.Boolean(), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["map_id"],
            ["final_architecture_maps.id"],
            name=op.f("fk_fa_observation_sources_map_id_final_architecture_maps"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("fa_observation_sources"),
        sa.UniqueConstraint(
            "map_id", "source_key", name=op.f("uq_fa_observation_sources_map_id")
        ),
    )
    _ix(
        "fa_observation_sources",
        [
            "map_id",
            "source_key",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "fa_pine_lanes",
        sa.Column("map_id", sa.String(length=36), nullable=False),
        sa.Column("lane_key", sa.String(length=64), nullable=False),
        sa.Column("lane_label", sa.String(length=255), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["map_id"],
            ["final_architecture_maps.id"],
            name=op.f("fk_fa_pine_lanes_map_id_final_architecture_maps"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("fa_pine_lanes"),
        sa.UniqueConstraint("map_id", "lane_key", name=op.f("uq_fa_pine_lanes_map_id")),
    )
    _ix(
        "fa_pine_lanes",
        [
            "map_id",
            "lane_key",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "fa_product_questions",
        sa.Column("map_id", sa.String(length=36), nullable=False),
        sa.Column("question_key", sa.String(length=64), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("addressed", sa.Boolean(), nullable=False),
        sa.Column("primary_stage_key", sa.String(length=64), nullable=True),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["map_id"],
            ["final_architecture_maps.id"],
            name=op.f("fk_fa_product_questions_map_id_final_architecture_maps"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("fa_product_questions"),
        sa.UniqueConstraint(
            "map_id", "question_key", name=op.f("uq_fa_product_questions_map_id")
        ),
    )
    _ix(
        "fa_product_questions",
        [
            "map_id",
            "question_key",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )


def downgrade() -> None:
    op.drop_table("fa_product_questions")
    op.drop_table("fa_pine_lanes")
    op.drop_table("fa_observation_sources")
    op.drop_table("fa_pipeline_stages")
    op.drop_table("final_architecture_maps")
