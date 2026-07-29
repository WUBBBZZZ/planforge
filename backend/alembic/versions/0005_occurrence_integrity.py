"""Deduplicate occurrences, add FK and unique constraint."""

import sqlalchemy as sa
from alembic import op

revision = "0005_occurrence_integrity"
down_revision = "0004_routine_schedule"
branch_labels = None
depends_on = None

_STATUS_PRIORITY = {
    "completed": 0,
    "skipped": 1,
    "pending": 2,
}


def _dedupe_occurrences(connection: sa.Connection) -> None:
    rows = connection.execute(
        sa.text(
            """
            SELECT id, routine_id, scheduled_date, status, created_at
            FROM occurrences
            ORDER BY routine_id, scheduled_date, created_at
            """
        )
    ).fetchall()

    groups: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    for row in rows:
        key = (row.routine_id, row.scheduled_date)
        groups.setdefault(key, []).append((row.id, row.status, row.created_at))

    for members in groups.values():
        if len(members) <= 1:
            continue
        members.sort(
            key=lambda item: (
                _STATUS_PRIORITY.get(item[1], 99),
                item[2] or "",
            )
        )
        for duplicate_id, _, _ in members[1:]:
            connection.execute(
                sa.text("DELETE FROM occurrences WHERE id = :id"),
                {"id": duplicate_id},
            )


def upgrade() -> None:
    """Remove duplicate occurrences and enforce uniqueness."""
    connection = op.get_bind()
    _dedupe_occurrences(connection)

    with op.batch_alter_table("occurrences") as batch_op:
        batch_op.create_foreign_key(
            "fk_occurrences_routine_id_routines",
            "routines",
            ["routine_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_unique_constraint(
            "uq_occurrences_routine_scheduled_date",
            ["routine_id", "scheduled_date"],
        )


def downgrade() -> None:
    """Remove occurrence integrity constraints."""
    with op.batch_alter_table("occurrences") as batch_op:
        batch_op.drop_constraint(
            "uq_occurrences_routine_scheduled_date",
            type_="unique",
        )
        batch_op.drop_constraint(
            "fk_occurrences_routine_id_routines",
            type_="foreignkey",
        )
