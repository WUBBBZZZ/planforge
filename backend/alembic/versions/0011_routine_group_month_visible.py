"""Add separate month visibility for routine groups."""

import sqlalchemy as sa
from alembic import op

revision = "0011_routine_group_month_visible"
down_revision = "0010_packing_lists"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("routine_groups") as batch_op:
        batch_op.add_column(
            sa.Column(
                "month_visible",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )

    # Preserve prior combined Week & Month checkbox behavior.
    op.execute(
        sa.text(
            """
            UPDATE routine_groups
            SET month_visible = week_visible
            """
        )
    )


def downgrade() -> None:
    with op.batch_alter_table("routine_groups") as batch_op:
        batch_op.drop_column("month_visible")
