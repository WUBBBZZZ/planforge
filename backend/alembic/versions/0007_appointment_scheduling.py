"""Extend appointments for all-day, multi-day, and lifecycle fields."""

import sqlalchemy as sa
from alembic import op

revision = "0007_appointment_scheduling"
down_revision = ("0005_occurrence_integrity", "0006_task_backlog_provenance")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add scheduling columns and relax timed instant nullability."""
    with op.batch_alter_table("appointments") as batch_op:
        batch_op.add_column(sa.Column("location", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("category", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("reminder_minutes", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("maintenance_definition_id", sa.String(length=36), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "is_all_day",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(sa.Column("start_date", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("end_date", sa.Date(), nullable=True))

    op.execute(
        """
        UPDATE appointments
        SET start_date = date(starts_at),
            end_date = date(ends_at)
        """
    )

    with op.batch_alter_table("appointments") as batch_op:
        batch_op.alter_column("start_date", nullable=False)
        batch_op.alter_column("end_date", nullable=False)
        batch_op.alter_column(
            "starts_at", existing_type=sa.DateTime(timezone=True), nullable=True
        )
        batch_op.alter_column(
            "ends_at", existing_type=sa.DateTime(timezone=True), nullable=True
        )
        batch_op.create_index(
            "ix_appointments_owner_status",
            ["owner_id", "status"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_appointments_maintenance_definition_id",
            "maintenance_definitions",
            ["maintenance_definition_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    """Revert appointment scheduling extensions."""
    with op.batch_alter_table("appointments") as batch_op:
        batch_op.drop_constraint(
            "fk_appointments_maintenance_definition_id",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_appointments_owner_status")
        batch_op.drop_column("end_date")
        batch_op.drop_column("start_date")
        batch_op.drop_column("is_all_day")
        batch_op.drop_column("maintenance_definition_id")
        batch_op.drop_column("reminder_minutes")
        batch_op.drop_column("category")
        batch_op.drop_column("location")
        batch_op.alter_column(
            "starts_at", existing_type=sa.DateTime(timezone=True), nullable=False
        )
        batch_op.alter_column(
            "ends_at", existing_type=sa.DateTime(timezone=True), nullable=False
        )
