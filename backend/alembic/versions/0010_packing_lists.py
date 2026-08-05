"""Add packing lists and entries."""

import sqlalchemy as sa
from alembic import op

revision = "0010_packing_lists"
down_revision = "0009_routine_groups"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "packing_lists",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
        "ix_packing_lists_owner_sort",
        "packing_lists",
        ["owner_id", "sort_order"],
    )

    op.create_table(
        "packing_list_entries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("list_id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("entry_type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "is_checked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("answer", sa.String(length=8), nullable=True),
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
            ["list_id"],
            ["packing_lists.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_packing_list_entries_list_sort",
        "packing_list_entries",
        ["list_id", "sort_order"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_packing_list_entries_list_sort", table_name="packing_list_entries"
    )
    op.drop_table("packing_list_entries")
    op.drop_index("ix_packing_lists_owner_sort", table_name="packing_lists")
    op.drop_table("packing_lists")
