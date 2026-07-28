"""Add routine schedule fields and start date."""

import sqlalchemy as sa
from alembic import op

revision = "0004_routine_schedule"
down_revision = "0003_planner_entities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add schedule type, monthly day, interval, and starts_on to routines."""
    with op.batch_alter_table("routines") as batch_op:
        batch_op.add_column(
            sa.Column(
                "schedule_type",
                sa.String(length=20),
                nullable=False,
                server_default="weekly",
            )
        )
        batch_op.add_column(sa.Column("day_of_month", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "interval_weeks",
                sa.Integer(),
                nullable=False,
                server_default="1",
            )
        )
        batch_op.add_column(sa.Column("starts_on", sa.Date(), nullable=True))


def downgrade() -> None:
    """Remove routine schedule fields."""
    with op.batch_alter_table("routines") as batch_op:
        batch_op.drop_column("starts_on")
        batch_op.drop_column("interval_weeks")
        batch_op.drop_column("day_of_month")
        batch_op.drop_column("schedule_type")
