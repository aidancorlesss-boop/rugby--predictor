import sqlite3

import pytest

from src.db.init_db import init_db
from src.db.normalize import normalize_name
from src.db.teams import (
    UnknownTeamError,
    load_aliases,
    load_teams,
    resolve_team_id,
)


@pytest.fixture
def conn(tmp_path):
    db = tmp_path / "t.db"
    init_db(db)
    c = sqlite3.connect(db)
    c.execute("PRAGMA foreign_keys = ON")
    teams = tmp_path / "teams.csv"
    teams.write_text("name,country\nBordeaux Bègles,France\nLeinster,Ireland\n", encoding="utf-8")
    aliases = tmp_path / "aliases.csv"
    aliases.write_text("alias,team\nUBB,Bordeaux Bègles\n", encoding="utf-8")
    load_teams(c, teams)
    load_aliases(c, aliases)
    yield c
    c.close()


def test_normalize_strips_accents_and_case():
    assert normalize_name("  Bordeaux   Bègles ") == "bordeaux begles"


def test_accent_and_case_variants_resolve_to_same_team(conn):
    assert resolve_team_id(conn, "bordeaux begles") == resolve_team_id(conn, "Bordeaux Bègles")


def test_alias_resolves(conn):
    assert resolve_team_id(conn, "UBB") == resolve_team_id(conn, "Bordeaux Bègles")


def test_unknown_team_raises(conn):
    with pytest.raises(UnknownTeamError):
        resolve_team_id(conn, "Narnia Knights")


def test_loading_twice_does_not_duplicate(conn, tmp_path):
    load_teams(conn, tmp_path / "teams.csv")
    assert conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0] == 2
