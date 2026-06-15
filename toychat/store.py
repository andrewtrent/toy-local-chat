from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class SearchHit:
    kind: str
    rowid: int
    score: float
    title: str
    body: str
    created_at: str


SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    project TEXT DEFAULT 'toy-local-chat',
    tags TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL,
    tags TEXT DEFAULT ''
);

CREATE VIRTUAL TABLE IF NOT EXISTS message_fts USING fts5(
    content,
    content='messages',
    content_rowid='id'
);

CREATE VIRTUAL TABLE IF NOT EXISTS note_fts USING fts5(
    title,
    body,
    content='notes',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO message_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO message_fts(message_fts, rowid, content) VALUES('delete', old.id, old.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
    INSERT INTO message_fts(message_fts, rowid, content) VALUES('delete', old.id, old.content);
    INSERT INTO message_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
    INSERT INTO note_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
END;

CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
    INSERT INTO note_fts(note_fts, rowid, title, body) VALUES('delete', old.id, old.title, old.body);
END;

CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
    INSERT INTO note_fts(note_fts, rowid, title, body) VALUES('delete', old.id, old.title, old.body);
    INSERT INTO note_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
END;
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, db_path: Path | str = "memory.db") -> None:
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def add_message(self, role: str, content: str, *, tags: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO messages(role, content, created_at, tags) VALUES (?, ?, ?, ?)",
            (role, content, now_iso(), tags),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def add_note(self, title: str, body: str, *, tags: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO notes(title, body, created_at, tags) VALUES (?, ?, ?, ?)",
            (title, body, now_iso(), tags),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def recent_messages(self, limit: int = 12) -> list[sqlite3.Row]:
        return list(
            reversed(
                self.conn.execute(
                    "SELECT * FROM messages ORDER BY id DESC LIMIT ?", (limit,)
                ).fetchall()
            )
        )

    def search_messages(self, query: str, limit: int = 5) -> list[SearchHit]:
        rows = self.conn.execute(
            """
            SELECT m.id, bm25(message_fts) AS score, m.role, m.content, m.created_at
            FROM message_fts
            JOIN messages m ON m.id = message_fts.rowid
            WHERE message_fts MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
        return [
            SearchHit("message", r["id"], float(r["score"]), r["role"], r["content"], r["created_at"])
            for r in rows
        ]

    def search_notes(self, query: str, limit: int = 5) -> list[SearchHit]:
        rows = self.conn.execute(
            """
            SELECT n.id, bm25(note_fts) AS score, n.title, n.body, n.created_at
            FROM note_fts
            JOIN notes n ON n.id = note_fts.rowid
            WHERE note_fts MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
        return [
            SearchHit("note", r["id"], float(r["score"]), r["title"], r["body"], r["created_at"])
            for r in rows
        ]

    def close(self) -> None:
        self.conn.close()
