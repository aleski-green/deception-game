SHARED_SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at    TEXT,
    winner      TEXT
);

CREATE TABLE IF NOT EXISTS players (
    id              INTEGER NOT NULL,
    game_id         INTEGER NOT NULL REFERENCES games(id),
    name            TEXT NOT NULL,
    role            TEXT NOT NULL,
    alive           INTEGER NOT NULL DEFAULT 1,
    eliminated_round INTEGER,
    eliminated_phase TEXT,
    PRIMARY KEY (game_id, id)
);

CREATE TABLE IF NOT EXISTS freechat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id     INTEGER NOT NULL,
    round       INTEGER NOT NULL,
    sender_id   INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pitch_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id     INTEGER NOT NULL,
    round       INTEGER NOT NULL,
    speaker_id  INTEGER NOT NULL,
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS votes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id     INTEGER NOT NULL,
    round       INTEGER NOT NULL,
    voter_id    INTEGER NOT NULL,
    target_id   INTEGER NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS vote_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id         INTEGER NOT NULL,
    round           INTEGER NOT NULL,
    eliminated_id   INTEGER,
    revealed_role   TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS night_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id         INTEGER NOT NULL,
    round           INTEGER NOT NULL,
    killed_id       INTEGER,
    saved           INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

AGENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS thoughts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id     INTEGER NOT NULL,
    round       INTEGER NOT NULL,
    phase       TEXT NOT NULL,
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS suspicions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id     INTEGER NOT NULL,
    round       INTEGER NOT NULL,
    target_id   INTEGER NOT NULL,
    level       REAL NOT NULL,
    reasoning   TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS strategy (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id     INTEGER NOT NULL,
    round       INTEGER NOT NULL,
    phase       TEXT NOT NULL,
    plan        TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS known_facts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id     INTEGER NOT NULL,
    round       INTEGER NOT NULL,
    fact_type   TEXT NOT NULL,
    about_id    INTEGER,
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS diary (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id     INTEGER NOT NULL,
    round       INTEGER NOT NULL,
    phase       TEXT NOT NULL,
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS round_summaries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id     INTEGER NOT NULL,
    round       INTEGER NOT NULL,
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS positions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id     INTEGER NOT NULL,
    round       INTEGER NOT NULL,
    phase       TEXT NOT NULL,
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""
