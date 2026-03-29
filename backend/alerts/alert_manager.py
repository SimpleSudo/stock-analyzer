"""
价格告警管理
- SQLite 持久化告警配置
- 后台定时检查价格触发告警
- SSE 推送已触发告警
"""
import sqlite3
import os
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Dict
from collections import deque

logger = logging.getLogger(__name__)

_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")
_DB_PATH = os.path.join(_DB_DIR, "stock_analyzer.db")


class AlertManager:
    def __init__(self, db_path: str = _DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        # 最近触发的告警队列（供 SSE 推送）
        self._triggered_queue: deque = deque(maxlen=100)
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
                    created_at TEXT NOT NULL,
                    triggered_at TEXT,
                    user_id TEXT DEFAULT 'default'
                )
            """)
            # 兼容旧表：添加可能缺少的列
            try:
                conn.execute("ALTER TABLE alerts ADD COLUMN triggered_at TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE alerts ADD COLUMN user_id TEXT DEFAULT 'default'")
            except sqlite3.OperationalError:
                pass

    def add(self, symbol: str, target_price: float, direction: str = "above",
            note: Optional[str] = None, user_id: str = "default") -> str:
        alert_id = str(uuid.uuid4())[:8]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO alerts (id, symbol, target_price, direction, note, created_at, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (alert_id, symbol, target_price, direction, note, datetime.now().isoformat(), user_id),
            )
        return alert_id

    def remove(self, alert_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))

    def get_all(self, symbol: Optional[str] = None, user_id: str = "default") -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if symbol:
                rows = conn.execute(
                    "SELECT * FROM alerts WHERE symbol = ? AND user_id = ? ORDER BY created_at DESC",
                    (symbol, user_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM alerts WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,),
                ).fetchall()
            return [dict(r) for r in rows]

    def get_pending_alerts(self) -> List[Dict]:
        """获取所有未触发的告警"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM alerts WHERE triggered = 0"
            ).fetchall()
            return [dict(r) for r in rows]

    def mark_triggered(self, alert_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE alerts SET triggered = 1, triggered_at = ? WHERE id = ?",
                (datetime.now().isoformat(), alert_id),
            )

    def check_and_trigger(self, price_map: Dict[str, float]) -> List[Dict]:
        """
        检查所有未触发告警，匹配当前价格。
        :param price_map: {symbol: current_price}
        :return: 本次新触发的告警列表
        """
        pending = self.get_pending_alerts()
        triggered = []

        for alert in pending:
            symbol = alert["symbol"]
            current_price = price_map.get(symbol)
            if current_price is None:
                continue

            target = alert["target_price"]
            direction = alert["direction"]

            hit = False
            if direction == "above" and current_price >= target:
                hit = True
            elif direction == "below" and current_price <= target:
                hit = True

            if hit:
                self.mark_triggered(alert["id"])
                alert["current_price"] = current_price
                alert["triggered_at"] = datetime.now().isoformat()
                triggered.append(alert)
                self._triggered_queue.append(alert)
                logger.info("告警触发: %s %s %s (当前价 %.2f, 目标价 %.2f)",
                            alert["id"], symbol, direction, current_price, target)

        return triggered

    def pop_triggered(self) -> List[Dict]:
        """弹出最近触发的告警（供 SSE 推送）"""
        items = list(self._triggered_queue)
        self._triggered_queue.clear()
        return items


# 全局实例
alert_manager = AlertManager()
