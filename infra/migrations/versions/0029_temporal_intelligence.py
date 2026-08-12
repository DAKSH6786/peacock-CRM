"""Peacock Temporal Intelligence — Visibility Timeline + change points

Revision ID: 0029_temporal_intelligence
Revises: 0028_learning_engine2
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0029_temporal_intelligence"
down_revision: Union[str, None] = "0028_learning_engine2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def upgrade() -> None:
    op.create_table(
        "temporal_timelines",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("analysis_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("noise_guardrail", sa.Text(), nullable=False),
        sa.Column("events_count", sa.Integer(), nullable=False),
        sa.Column("change_points_count", sa.Integer(), nullable=False),
        sa.Column("alerts_suppressed", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_temporal_timelines_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_temporal_timelines_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_temporal_timelines_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_temporal_timelines_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_temporal_timelines")),
    )
    _ix(
        "temporal_timelines",
        [
            "website_id",
            "client_brand",
            "analysis_status",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "ti_timeline_events",
        sa.Column("timeline_id", sa.String(length=36), nullable=False),
        sa.Column("event_kind", sa.String(length=64), nullable=False),
        sa.Column("event_label", sa.String(length=255), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("magnitude", sa.Float(), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("metric_key", sa.String(length=128), nullable=True),
        sa.Column("metric_value", sa.Float(), nullable=True),
        sa.Column("source_ref", sa.String(length=255), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_ti_timeline_events_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_ti_timeline_events_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["timeline_id"], ["temporal_timelines.id"], name=op.f("fk_ti_timeline_events_timeline_id_temporal_timelines"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_ti_timeline_events_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ti_timeline_events")),
    )
    _ix(
        "ti_timeline_events",
        [
            "timeline_id",
            "event_kind",
            "occurred_at",
            "metric_key",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "ti_change_points",
        sa.Column("timeline_id", sa.String(length=36), nullable=False),
        sa.Column("metric_key", sa.String(length=128), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("effect_size", sa.Float(), nullable=False),
        sa.Column("baseline_mean", sa.Float(), nullable=False),
        sa.Column("baseline_std", sa.Float(), nullable=False),
        sa.Column("post_mean", sa.Float(), nullable=False),
        sa.Column("is_alert", sa.Boolean(), nullable=False),
        sa.Column("suppressed_as_noise", sa.Boolean(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_ti_change_points_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_ti_change_points_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["timeline_id"], ["temporal_timelines.id"], name=op.f("fk_ti_change_points_timeline_id_temporal_timelines"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_ti_change_points_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ti_change_points")),
        sa.UniqueConstraint(
            "timeline_id",
            "metric_key",
            "detected_at",
            name=op.f("uq_ti_change_points_timeline_id"),
        ),
    )
    _ix(
        "ti_change_points",
        [
            "timeline_id",
            "metric_key",
            "detected_at",
            "is_alert",
            "suppressed_as_noise",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "ti_query_answers",
        sa.Column("timeline_id", sa.String(length=36), nullable=False),
        sa.Column("intent", sa.String(length=64), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("supporting_event_ids", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_ti_query_answers_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_ti_query_answers_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["timeline_id"], ["temporal_timelines.id"], name=op.f("fk_ti_query_answers_timeline_id_temporal_timelines"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_ti_query_answers_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ti_query_answers")),
    )
    _ix(
        "ti_query_answers",
        ["timeline_id", "intent", "organisation_id", "workspace_id", "created_by", "status"],
    )


def downgrade() -> None:
    op.drop_table("ti_query_answers")
    op.drop_table("ti_change_points")
    op.drop_table("ti_timeline_events")
    op.drop_table("temporal_timelines")
