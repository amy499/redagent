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
            markers        TEXT NOT NULL
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
    """)
    conn.commit()
    conn.close()
