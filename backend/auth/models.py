"""用户模型 - SQLite 存储"""
import sqlite3
import os
import uuid
from datetime import datetime
from typing import Optional, Dict

_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")
_DB_PATH = os.path.join(_DB_DIR, "stock_analyzer.db")


class UserStore:
    def __init__(self, db_path: str = _DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

    def create(self, username: str, password_hash: str) -> str:
        user_id = str(uuid.uuid4())[:12]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (user_id, username, password_hash, datetime.now().isoformat()),
            )
        return user_id

    def get_by_username(self, username: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            return dict(row) if row else None

    def get_by_id(self, user_id: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row) if row else None


user_store = UserStore()
