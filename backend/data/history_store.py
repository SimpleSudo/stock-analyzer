"""
分析历史记录存储（SQLite）
"""
import sqlite3
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")
_DB_PATH = os.path.join(_DB_DIR, "stock_analyzer.db")


class HistoryStore:
    def __init__(self, db_path: str = _DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    name TEXT,
                    signal TEXT,
                    score REAL,
                    price REAL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_symbol ON analysis_history(symbol)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_created ON analysis_history(created_at DESC)
            """)

    def add(self, symbol: str, name: str, signal: str, score: float, price: float):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO analysis_history (symbol, name, signal, score, price, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (symbol, name, signal, score, price, datetime.now().isoformat()),
            )

    def get_all(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if symbol:
                rows = conn.execute(
                    "SELECT * FROM analysis_history WHERE symbol = ? ORDER BY created_at DESC LIMIT ?",
                    (symbol, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM analysis_history ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
