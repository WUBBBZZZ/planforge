import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parents[1] / "data" / "planforge.db"
conn = sqlite3.connect(db_path)
tables = [
    row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
]
print("tables:", tables)
if "alembic_version" in tables:
    print("alembic_version:", list(conn.execute("SELECT * FROM alembic_version")))
if "routines" in tables:
    print(
        "routines columns:",
        [row[1] for row in conn.execute("PRAGMA table_info(routines)")],
    )
