import sqlite3

from src.db.init_db import DB_PATH, init_db
from src.db.teams import load_aliases, load_competitions, load_teams


def main() -> None:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        load_competitions(conn)
        load_teams(conn)
        load_aliases(conn)
        teams = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
        aliases = conn.execute("SELECT COUNT(*) FROM team_aliases").fetchone()[0]
    print(f"Loaded {teams} teams and {aliases} aliases into {DB_PATH}")


if __name__ == "__main__":
    main()
