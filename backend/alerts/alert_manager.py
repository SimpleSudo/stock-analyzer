"""
价格告警管理
- SQLite 持久化告警配置
- 提供增删查接口
"""
import sqlite3
import os
import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")
_DB_PATH = os.path.join(_DB_DIR, "stock_analyzer.db")


class AlertManager:
    def __init__(self, db_path: str = _DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    target_price REAL NOT NULL,
                    direction TEXT NOT NULL DEFAULT 'above',
                    note TEXT,
                    triggered INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

    def add(self, symbol: str, target_price: float, direction: str = "above", note: Optional[str] = None) -> str:
        alert_id = str(uuid.uuid4())[:8]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO alerts (id, symbol, target_price, direction, note, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (alert_id, symbol, target_price, direction, note, datetime.now().isoformat()),
            )
        return alert_id

    def remove(self, alert_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))

    def get_all(self, symbol: Optional[str] = None) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if symbol:
                rows = conn.execute(
                    "SELECT * FROM alerts WHERE symbol = ? ORDER BY created_at DESC", (symbol,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM alerts ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def mark_triggered(self, alert_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE alerts SET triggered = 1 WHERE id = ?", (alert_id,))


# 全局实例
alert_manager = AlertManager()
