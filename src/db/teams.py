import csv
import sqlite3
from pathlib import Path

from src.db.normalize import normalize_name

SEED_DIR = Path("data/seed")

COMPETITIONS = [
    "Champions Cup",
    "Challenge Cup",
    "URC",
    "Premiership",
    "Top 14",
]


class UnknownTeamError(KeyError):
    """Raised when a team name from a data source has no alias yet."""


def load_competitions(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT OR IGNORE INTO competitions(name) VALUES (?)",
        [(c,) for c in COMPETITIONS],
    )


def _team_id(conn: sqlite3.Connection, name: str) -> int:
    row = conn.execute("SELECT team_id FROM teams WHERE name = ?", (name,)).fetchone()
    if row is None:
        raise ValueError(f"Unknown canonical team name: {name!r}")
    return row[0]


def load_teams(conn: sqlite3.Connection, csv_path: Path = SEED_DIR / "teams.csv") -> None:
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["name"].strip()
            conn.execute(
                "INSERT OR IGNORE INTO teams(name, country) VALUES (?, ?)",
                (name, row["country"].strip()),
            )
            conn.execute(
                "INSERT OR IGNORE INTO team_aliases(alias, team_id) VALUES (?, ?)",
                (normalize_name(name), _team_id(conn, name)),
            )


def load_aliases(conn: sqlite3.Connection, csv_path: Path = SEED_DIR / "team_aliases.csv") -> None:
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            conn.execute(
                "INSERT OR IGNORE INTO team_aliases(alias, team_id) VALUES (?, ?)",
                (normalize_name(row["alias"]), _team_id(conn, row["team"].strip())),
            )


def resolve_team_id(conn: sqlite3.Connection, raw_name: str) -> int:
    row = conn.execute(
        "SELECT team_id FROM team_aliases WHERE alias = ?",
        (normalize_name(raw_name),),
    ).fetchone()
    if row is None:
        raise UnknownTeamError(raw_name)
    return row[0]
