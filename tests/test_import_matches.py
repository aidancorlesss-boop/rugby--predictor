import sqlite3

import pytest

from src.db.init_db import init_db
from src.db.teams import load_competitions, load_teams
from src.ingest.matches import (
    REQUIRED_COLUMNS,
    ImportValidationError,
    import_matches_csv,
)


def write_csv(path, rows):
    lines = [",".join(REQUIRED_COLUMNS)] + [",".join(r) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def conn(tmp_path):
    db = tmp_path / "t.db"
    init_db(db)
    c = sqlite3.connect(db)
    c.execute("PRAGMA foreign_keys = ON")
    load_competitions(c)
    teams = tmp_path / "teams.csv"
    teams.write_text("name,country\nLeinster,Ireland\nMunster,Ireland\n", encoding="utf-8")
    load_teams(c, teams)
    yield c
    c.close()


# date, season, competition, stage, home, away, hs, as, neutral, source
GOOD = ["2026-01-10", "2025-26", "URC", "Round 1", "Leinster", "Munster", "20", "10", "0", "test"]


def test_valid_rows_are_imported(conn, tmp_path):
    f = write_csv(tmp_path / "m.csv", [GOOD])
    result = import_matches_csv(conn, f)
    assert result["inserted"] == 1
    assert conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0] == 1


def test_reimport_updates_instead_of_duplicating(conn, tmp_path):
    unplayed = GOOD[:6] + ["", ""] + GOOD[8:]
    import_matches_csv(conn, write_csv(tmp_path / "a.csv", [unplayed]))
    result = import_matches_csv(conn, write_csv(tmp_path / "b.csv", [GOOD]))
    assert result["updated"] == 1
    rows = conn.execute("SELECT home_score, away_score FROM matches").fetchall()
    assert rows == [(20, 10)]


def test_unknown_team_aborts_everything(conn, tmp_path):
    bad = GOOD[:4] + ["Narnia Knights"] + GOOD[5:]
    f = write_csv(tmp_path / "m.csv", [GOOD, bad])
    with pytest.raises(ImportValidationError, match="Narnia Knights"):
        import_matches_csv(conn, f)
    assert conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0] == 0


def test_same_team_both_sides_rejected(conn, tmp_path):
    bad = GOOD[:5] + ["Leinster"] + GOOD[6:]
    with pytest.raises(ImportValidationError, match="same team"):
        import_matches_csv(conn, write_csv(tmp_path / "m.csv", [bad]))


def test_bad_date_rejected(conn, tmp_path):
    bad = ["10/01/2026"] + GOOD[1:]
    with pytest.raises(ImportValidationError, match="YYYY-MM-DD"):
        import_matches_csv(conn, write_csv(tmp_path / "m.csv", [bad]))
