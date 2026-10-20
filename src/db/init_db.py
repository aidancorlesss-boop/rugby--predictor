import sqlite3
from pathlib import Path

DB_PATH = Path("data/rugby.db")
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA_PATH.read_text())
    print(f"Database ready at {db_path}")


if __name__ == "__main__":
    init_db()
