"""Extend maintenance for long-term scheduling subsystem."""

import sqlalchemy as sa
from alembic import op

revision = "0008_maintenance_subsystem"
down_revision = "0007_appointment_scheduling"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add maintenance completions and extended definition fields."""
    op.create_table(
        "maintenance_completions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("maintenance_definition_id", sa.String(length=36), nullable=False),
        sa.Column("completed_on", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_voided", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("superseded_by_id", sa.String(length=36), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["maintenance_definition_id"],
            ["maintenance_definitions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["superseded_by_id"],
            ["maintenance_completions.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_maintenance_completions_definition_date",
        "maintenance_completions",
        ["maintenance_definition_id", "completed_on"],
    )

    with op.batch_alter_table("maintenance_definitions") as batch_op:
        batch_op.add_column(sa.Column("category", sa.String(length=120), nullable=True))
        batch_op.add_column(
            sa.Column("interval_unit", sa.String(length=10), nullable=True)
        )
        batch_op.add_column(sa.Column("interval_value", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("last_completed_date", sa.Date(), nullable=True))
        batch_op.add_column(
            sa.Column("next_action_status", sa.String(length=20), nullable=True)
        )
        batch_op.add_column(
            sa.Column("linked_appointment_id", sa.String(length=36), nullable=True)
        )
        batch_op.add_column(
            sa.Column("scheduling_reminder_date", sa.Date(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("reminder_offset_days", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "lead_time_days",
                sa.Integer(),
                nullable=False,
                server_default="30",
            )
        )

    op.execute(
        """
        UPDATE maintenance_definitions
        SET interval_unit = 'days',
            interval_value = interval_days,
            last_completed_date = date(last_completed_at),
            next_action_status = CASE
                WHEN status = 'archived' THEN 'not_applicable'
                WHEN last_completed_at IS NOT NULL THEN 'needs_scheduling'
                ELSE 'no_next_date'
            END
        """
    )

    with op.batch_alter_table("maintenance_definitions") as batch_op:
        batch_op.alter_column("interval_unit", nullable=False)
        batch_op.alter_column("next_action_status", nullable=False)
        batch_op.drop_column("interval_days")
        batch_op.drop_column("last_completed_at")
        batch_op.create_index(
            "ix_maintenance_owner_next_action",
            ["owner_id", "next_action_status"],
            unique=False,
        )
        batch_op.create_unique_constraint(
            "uq_maintenance_linked_appointment",
            ["linked_appointment_id"],
        )
        batch_op.create_foreign_key(
            "fk_maintenance_linked_appointment_id",
            "appointments",
            ["linked_appointment_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    """Revert maintenance subsystem extensions."""
    with op.batch_alter_table("maintenance_definitions") as batch_op:
        batch_op.drop_constraint(
            "fk_maintenance_linked_appointment_id",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "uq_maintenance_linked_appointment",
            type_="unique",
        )
        batch_op.drop_index("ix_maintenance_owner_next_action")
        batch_op.add_column(sa.Column("interval_days", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("last_completed_at", sa.DateTime(timezone=True), nullable=True)
        )

    op.execute(
        """
        UPDATE maintenance_definitions
        SET interval_days = COALESCE(interval_value, 90),
            last_completed_at = datetime(last_completed_date)
        """
    )

    with op.batch_alter_table("maintenance_definitions") as batch_op:
        batch_op.alter_column("interval_days", nullable=False)
        batch_op.drop_column("lead_time_days")
        batch_op.drop_column("reminder_offset_days")
        batch_op.drop_column("scheduling_reminder_date")
        batch_op.drop_column("linked_appointment_id")
        batch_op.drop_column("next_action_status")
        batch_op.drop_column("last_completed_date")
        batch_op.drop_column("interval_value")
        batch_op.drop_column("interval_unit")
        batch_op.drop_column("category")

    op.drop_index(
        "ix_maintenance_completions_definition_date",
        table_name="maintenance_completions",
    )
    op.drop_table("maintenance_completions")
