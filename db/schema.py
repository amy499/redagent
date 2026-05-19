import os
import sqlite3

DB_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "redagent.db"))


def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS attacks (
            id          TEXT PRIMARY KEY,
            category    TEXT NOT NULL,
            subcategory TEXT,
            technique   TEXT,
            prompt_text TEXT NOT NULL,
            severity    TEXT,
            notes       TEXT,
            target      TEXT DEFAULT 'general'
        );

        CREATE TABLE IF NOT EXISTS targets (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT NOT NULL,
            endpoint_url   TEXT NOT NULL,
            system_prompt  TEXT NOT NULL,
            markers        TEXT NOT NULL,
            request_field  TEXT DEFAULT 'message',
            response_field TEXT DEFAULT 'response',
            auth_header    TEXT DEFAULT NULL
        );

        CREATE TABLE IF NOT EXISTS results (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            attack_id      TEXT,
            target_id      INTEGER,
            prompt_sent    TEXT NOT NULL,
            bot_response   TEXT,
            success        INTEGER DEFAULT 0,
            severity       INTEGER DEFAULT 0,
            leaked_markers TEXT,
            reason         TEXT,
            category       TEXT,
            timestamp      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reports (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            filename       TEXT NOT NULL,
            target_id      INTEGER,
            total_attacks  INTEGER,
            successes      INTEGER,
            breach_rate    REAL,
            created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id      INTEGER,
            started_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
            ended_at       DATETIME,
            total_messages INTEGER DEFAULT 0,
            attacks_fired  INTEGER DEFAULT 0,
            breaches       INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS messages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      INTEGER NOT NULL,
            role            TEXT NOT NULL,
            content         TEXT NOT NULL,
            is_attack       INTEGER DEFAULT 0,
            attack_category TEXT,
            success         INTEGER,
            severity        INTEGER,
            leaked_markers  TEXT,
            reason          TEXT,
            mitigation      TEXT,
            timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # Add columns to existing targets table (no-op if already present)
    for stmt in [
        "ALTER TABLE targets ADD COLUMN request_field  TEXT DEFAULT 'message'",
        "ALTER TABLE targets ADD COLUMN response_field TEXT DEFAULT 'response'",
        "ALTER TABLE targets ADD COLUMN auth_header    TEXT DEFAULT NULL",
    ]:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            pass  # column already exists

    conn.commit()
    conn.close()
