import sqlite3
import pytest
from src.db.init_db import init_db


def test_tables_exist(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    with sqlite3.connect(db) as conn:
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"teams", "team_aliases", "matches", "competitions"} <= tables


def test_duplicate_match_rejected(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("INSERT INTO teams(team_id, name) VALUES (1,'A'),(2,'B')")
        conn.execute("INSERT INTO competitions(competition_id, name) VALUES (1,'Test Cup')")
        row = ("2026-10-17", "2026-27", 1, 1, 2, 20, 10, "test")
        sql = """INSERT INTO matches(match_date, season, competition_id,
                 home_team_id, away_team_id, home_score, away_score, source)
                 VALUES (?,?,?,?,?,?,?,?)"""
        conn.execute(sql, row)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(sql, row)
