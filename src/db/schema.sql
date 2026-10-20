PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS teams (
    team_id     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    country     TEXT
);

CREATE TABLE IF NOT EXISTS team_seasons (
    team_id     INTEGER NOT NULL REFERENCES teams(team_id),
    season      TEXT NOT NULL,
    league      TEXT NOT NULL,
    PRIMARY KEY (team_id, season)
);

CREATE TABLE IF NOT EXISTS team_aliases (
    alias       TEXT PRIMARY KEY,
    team_id     INTEGER NOT NULL REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS venues (
    venue_id    INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    city        TEXT,
    country     TEXT,
    lat         REAL,
    lon         REAL
);

CREATE TABLE IF NOT EXISTS competitions (
    competition_id INTEGER PRIMARY KEY,
    name           TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS matches (
    match_id       INTEGER PRIMARY KEY,
    match_date     TEXT NOT NULL,
    season         TEXT NOT NULL,
    competition_id INTEGER NOT NULL REFERENCES competitions(competition_id),
    stage          TEXT,
    home_team_id   INTEGER NOT NULL REFERENCES teams(team_id),
    away_team_id   INTEGER NOT NULL REFERENCES teams(team_id),
    home_score     INTEGER,
    away_score     INTEGER,
    venue_id       INTEGER REFERENCES venues(venue_id),
    neutral_venue  INTEGER NOT NULL DEFAULT 0,
    source         TEXT NOT NULL,
    CHECK (home_team_id <> away_team_id),
    UNIQUE (match_date, home_team_id, away_team_id, competition_id)
);

CREATE INDEX IF NOT EXISTS idx_matches_date   ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_season ON matches(season);
