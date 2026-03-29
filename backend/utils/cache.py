"""
内存缓存（TTL 机制）
- 避免短时间内重复请求 AKShare
- 线程安全
"""
import time
import threading
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TTLCache:
    """简单的线程安全 TTL 缓存"""

    def __init__(self, default_ttl: int = 300):
        """
        :param default_ttl: 默认过期时间（秒），默认 5 分钟
        """
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expire_at = entry
            if time.time() > expire_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        ttl = ttl or self.default_ttl
        with self._lock:
            self._store[key] = (value, time.time() + ttl)

    def delete(self, key: str):
        with self._lock:
            self._store.pop(key, None)

    def clear(self):
        with self._lock:
            self._store.clear()

    def cleanup(self):
        """清理过期条目"""
        now = time.time()
        with self._lock:
            expired = [k for k, (_, exp) in self._store.items() if now > exp]
            for k in expired:
                del self._store[k]


# 全局缓存实例
stock_data_cache = TTLCache(default_ttl=300)       # 行情数据 5 分钟
fundamental_cache = TTLCache(default_ttl=3600)      # 基本面数据 1 小时
