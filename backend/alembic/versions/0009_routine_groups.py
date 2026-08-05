"""Add routine groups and routine ordering."""

import uuid

import sqlalchemy as sa
from alembic import op

revision = "0009_routine_groups"
down_revision = "0008_maintenance_subsystem"
branch_labels = None
depends_on = None

MISC_GROUP_NAME = "Misc"


def upgrade() -> None:
    op.create_table(
        "routine_groups",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "week_visible",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "is_system",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
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
        sa.UniqueConstraint("owner_id", "name", name="uq_routine_groups_owner_name"),
    )
    op.create_index(
        "ix_routine_groups_owner_sort",
        "routine_groups",
        ["owner_id", "sort_order"],
    )

    with op.batch_alter_table("routines") as batch_op:
        batch_op.add_column(sa.Column("group_id", sa.String(length=36), nullable=True))
        batch_op.add_column(
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.create_foreign_key(
            "fk_routines_group_id",
            "routine_groups",
            ["group_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # Assign each owner's routines to a default Misc group.
    connection = op.get_bind()
    owner_rows = connection.execute(
        sa.text("SELECT DISTINCT owner_id FROM routines")
    ).fetchall()
    for (owner_id,) in owner_rows:
        misc_id = str(uuid.uuid4())
        connection.execute(
            sa.text(
                """
                INSERT INTO routine_groups (
                    id, owner_id, name, sort_order, week_visible, is_system
                ) VALUES (
                    :id, :owner_id, :name, 0, 0, 1
                )
                """
            ),
            {"id": misc_id, "owner_id": owner_id, "name": MISC_GROUP_NAME},
        )
        connection.execute(
            sa.text(
                """
                UPDATE routines
                SET group_id = :group_id
                WHERE owner_id = :owner_id AND group_id IS NULL
                """
            ),
            {"group_id": misc_id, "owner_id": owner_id},
        )


def downgrade() -> None:
    with op.batch_alter_table("routines") as batch_op:
        batch_op.drop_constraint("fk_routines_group_id", type_="foreignkey")
        batch_op.drop_column("sort_order")
        batch_op.drop_column("group_id")

    op.drop_index("ix_routine_groups_owner_sort", table_name="routine_groups")
    op.drop_table("routine_groups")
