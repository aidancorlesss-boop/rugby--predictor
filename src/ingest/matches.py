import csv
import sqlite3
from datetime import date
from pathlib import Path

from src.db.teams import UnknownTeamError, resolve_team_id

REQUIRED_COLUMNS = [
    "date", "season", "competition", "stage",
    "home_team", "away_team", "home_score", "away_score",
    "neutral", "source",
]

UPSERT_SQL = """
INSERT INTO matches (match_date, season, competition_id, stage,
                     home_team_id, away_team_id, home_score, away_score,
                     neutral_venue, source)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(match_date, home_team_id, away_team_id, competition_id)
DO UPDATE SET
    season = excluded.season,
    stage = excluded.stage,
    home_score = excluded.home_score,
    away_score = excluded.away_score,
    neutral_venue = excluded.neutral_venue,
    source = excluded.source
"""


class ImportValidationError(Exception):
    """Raised when a CSV has problems. Nothing is written when this happens."""


def _parse_score(value: str, line: int):
    value = (value or "").strip()
    if value == "":
        return None
    try:
        n = int(value)
    except ValueError:
        raise ValueError(f"line {line}: score {value!r} is not a whole number")
    if n < 0:
        raise ValueError(f"line {line}: score {n} is negative")
    return n


def import_matches_csv(conn: sqlite3.Connection, csv_path: Path) -> dict:
    competitions = dict(conn.execute("SELECT name, competition_id FROM competitions"))
    unknown_teams: set[str] = set()
    errors: list[str] = []
    rows_to_write = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ImportValidationError(f"CSV is missing columns: {missing}")

        for line, row in enumerate(reader, start=2):  # line 1 is the header
            try:
                match_date = date.fromisoformat(row["date"].strip()).isoformat()
            except ValueError:
                errors.append(f"line {line}: date {row['date']!r} is not YYYY-MM-DD")
                continue

            comp_name = row["competition"].strip()
            if comp_name not in competitions:
                errors.append(f"line {line}: unknown competition {comp_name!r}")
                continue

            team_ids = []
            for col in ("home_team", "away_team"):
                try:
                    team_ids.append(resolve_team_id(conn, row[col]))
                except UnknownTeamError:
                    unknown_teams.add(row[col].strip())
            if len(team_ids) != 2:
                continue  # unknown team(s) already recorded
            home_id, away_id = team_ids
            if home_id == away_id:
                errors.append(f"line {line}: home and away are the same team")
                continue

            try:
                home_score = _parse_score(row["home_score"], line)
                away_score = _parse_score(row["away_score"], line)
            except ValueError as e:
                errors.append(str(e))
                continue
            if (home_score is None) != (away_score is None):
                errors.append(f"line {line}: only one score filled in")
                continue

            neutral = 1 if row["neutral"].strip() in ("1", "true", "True", "yes") else 0
            rows_to_write.append((
                match_date, row["season"].strip(), competitions[comp_name],
                row["stage"].strip() or None, home_id, away_id,
                home_score, away_score, neutral, row["source"].strip(),
            ))

    if unknown_teams:
        errors.append(
            "Unknown team names (add them to data/seed/team_aliases.csv): "
            + ", ".join(sorted(unknown_teams))
        )
    if errors:
        raise ImportValidationError("\n".join(errors))

    before = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    conn.executemany(UPSERT_SQL, rows_to_write)
    after = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    return {
        "rows_in_file": len(rows_to_write),
        "inserted": after - before,
        "updated": len(rows_to_write) - (after - before),
    }
