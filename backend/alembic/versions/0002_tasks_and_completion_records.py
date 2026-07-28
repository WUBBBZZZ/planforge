"""Tasks and completion records tables."""

import sqlalchemy as sa
from alembic import op

revision = "0002_tasks_and_completion_records"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tasks and completion_records tables."""
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
    )
    op.create_index(
        "ix_tasks_owner_status_due_date",
        "tasks",
        ["owner_id", "status", "due_date"],
        unique=False,
    )
    op.create_index(
        "ix_tasks_owner_due_date",
        "tasks",
        ["owner_id", "due_date"],
        unique=False,
    )

    op.create_table(
        "completion_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_completion_records")),
    )
    op.create_index(
        "ix_completion_records_entity",
        "completion_records",
        ["entity_type", "entity_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop tasks and completion_records tables."""
    op.drop_index("ix_completion_records_entity", table_name="completion_records")
    op.drop_table("completion_records")
    op.drop_index("ix_tasks_owner_due_date", table_name="tasks")
    op.drop_index("ix_tasks_owner_status_due_date", table_name="tasks")
    op.drop_table("tasks")
