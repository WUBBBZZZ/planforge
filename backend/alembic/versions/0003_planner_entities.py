"""Planner entities beyond tasks and completion records."""

import sqlalchemy as sa
from alembic import op

revision = "0003_planner_entities"
down_revision = "0002_tasks_and_completion_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create backlog, routines, appointments, settings, targets, maintenance."""
    op.create_table(
        "backlog_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("promoted_entity_type", sa.String(length=32), nullable=True),
        sa.Column("promoted_entity_id", sa.String(length=36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_backlog_owner_status", "backlog_items", ["owner_id", "status"])

    op.create_table(
        "routines",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("days_of_week", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_routines_owner_status", "routines", ["owner_id", "status"])

    op.create_table(
        "occurrences",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("routine_id", sa.String(length=36), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_occurrences_owner_date", "occurrences", ["owner_id", "scheduled_date"]
    )
    op.create_index(
        "ix_occurrences_routine_date", "occurrences", ["routine_id", "scheduled_date"]
    )

    op.create_table(
        "appointments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_appointments_owner_starts", "appointments", ["owner_id", "starts_at"]
    )

    op.create_table(
        "settings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.String(length=256), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "key", name="uq_settings_owner_key"),
    )
    op.create_index("ix_settings_owner", "settings", ["owner_id"])

    op.create_table(
        "weekly_targets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("target_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_weekly_targets_owner_status", "weekly_targets", ["owner_id", "status"]
    )

    op.create_table(
        "maintenance_definitions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("last_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_maintenance_owner_status", "maintenance_definitions", ["owner_id", "status"]
    )
    op.create_index(
        "ix_maintenance_owner_due",
        "maintenance_definitions",
        ["owner_id", "next_due_date"],
    )


def downgrade() -> None:
    """Drop planner entity tables."""
    op.drop_index("ix_maintenance_owner_due", table_name="maintenance_definitions")
    op.drop_index("ix_maintenance_owner_status", table_name="maintenance_definitions")
    op.drop_table("maintenance_definitions")
    op.drop_index("ix_weekly_targets_owner_status", table_name="weekly_targets")
    op.drop_table("weekly_targets")
    op.drop_index("ix_settings_owner", table_name="settings")
    op.drop_table("settings")
    op.drop_index("ix_appointments_owner_starts", table_name="appointments")
    op.drop_table("appointments")
    op.drop_index("ix_occurrences_routine_date", table_name="occurrences")
    op.drop_index("ix_occurrences_owner_date", table_name="occurrences")
    op.drop_table("occurrences")
    op.drop_index("ix_routines_owner_status", table_name="routines")
    op.drop_table("routines")
    op.drop_index("ix_backlog_owner_status", table_name="backlog_items")
    op.drop_table("backlog_items")
