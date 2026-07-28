"""Add backlog provenance fields for task moves."""

import sqlalchemy as sa
from alembic import op

revision = "0006_task_backlog_provenance"
down_revision = "0004_routine_schedule"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add source entity columns for task-to-backlog moves."""
    with op.batch_alter_table("backlog_items") as batch_op:
        batch_op.add_column(
            sa.Column("source_entity_type", sa.String(length=32), nullable=True)
        )
        batch_op.add_column(
            sa.Column("source_entity_id", sa.String(length=36), nullable=True)
        )
        batch_op.create_index(
            "ix_backlog_source_entity",
            ["owner_id", "source_entity_type", "source_entity_id"],
        )


def downgrade() -> None:
    """Remove backlog provenance fields."""
    with op.batch_alter_table("backlog_items") as batch_op:
        batch_op.drop_index("ix_backlog_source_entity")
        batch_op.drop_column("source_entity_id")
        batch_op.drop_column("source_entity_type")
