"""
统一日志配置
使用方法：在各模块头部 import logging; logger = logging.getLogger(__name__)
"""
import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """
    配置全局日志格式和级别。
    应在应用启动时调用一次。
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(log_level)

    # 避免重复添加 handler
    if not root.handlers:
        root.addHandler(handler)

    # 降低第三方库日志级别
    for noisy in ("httpx", "httpcore", "urllib3", "akshare", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
