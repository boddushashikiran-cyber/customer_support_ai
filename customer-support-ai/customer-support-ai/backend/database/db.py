"""
SQLite database layer.
Handles: users, sessions, conversation memory.
Swap this out for MongoDB/PostgreSQL later if needed -- the interface
(the functions below) is what the rest of the app depends on, not the
storage engine itself.
"""
import sqlite3
import uuid
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "customer_support.db"


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                username TEXT NOT NULL,
                role TEXT NOT NULL,           -- 'user' or 'assistant'
                content TEXT NOT NULL,
                agent TEXT,                   -- which agent answered (nullable)
                timestamp TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                username TEXT NOT NULL,
                issue TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ---------- Users ----------

def create_user(username: str, hashed_password: str) -> str:
    user_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (id, username, hashed_password, created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, hashed_password, datetime.utcnow().isoformat()),
        )
        conn.commit()
    return user_id


def get_user_by_username(username: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None


# ---------- Conversation memory ----------

def save_message(session_id: str, username: str, role: str, content: str, agent: str = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO conversations (id, session_id, username, role, content, agent, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), session_id, username, role, content, agent, datetime.utcnow().isoformat()),
        )
        conn.commit()


def get_history(session_id: str, limit: int = 20):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM conversations WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- Tickets (for escalation) ----------

def create_ticket(session_id: str, username: str, issue: str) -> str:
    ticket_id = str(uuid.uuid4())[:8]
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO tickets (id, session_id, username, issue, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (ticket_id, session_id, username, issue, "open", datetime.utcnow().isoformat()),
        )
        conn.commit()
    return ticket_id
