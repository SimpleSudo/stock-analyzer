"""
自选股存储（SQLite）
"""
import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")
_DB_PATH = os.path.join(_DB_DIR, "stock_analyzer.db")


class WatchlistStore:
    def __init__(self, db_path: str = _DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    symbol TEXT PRIMARY KEY,
                    name TEXT,
                    added_at TEXT NOT NULL
                )
            """)

    def add(self, symbol: str, name: str = ""):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO watchlist (symbol, name, added_at) VALUES (?, ?, ?)",
                (symbol, name, datetime.now().isoformat()),
            )

    def remove(self, symbol: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol,))

    def get_all(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM watchlist ORDER BY added_at DESC").fetchall()
            return [dict(r) for r in rows]

    def exists(self, symbol: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT 1 FROM watchlist WHERE symbol = ?", (symbol,)).fetchone()
            return row is not None
