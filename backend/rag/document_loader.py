"""
文档加载器 - 从东方财富获取个股公告和研报摘要
"""
import logging
import akshare as ak
import pandas as pd
from typing import List, Dict
from utils.cache import stock_data_cache

logger = logging.getLogger(__name__)


def load_stock_announcements(symbol: str, limit: int = 20) -> List[Dict]:
    """获取个股公告（缓存 2 小时）"""
    cache_key = f"rag:announce:{symbol}"
    cached = stock_data_cache.get(cache_key)
    if cached is not None:
        return cached

    docs = []
    try:
        # 个股新闻（包含公告）
        news_df = ak.stock_news_em(symbol=symbol)
        if news_df is not None and not news_df.empty:
            for _, row in news_df.head(limit).iterrows():
                docs.append({
                    "title": str(row.get("新闻标题", "")),
                    "content": str(row.get("新闻内容", ""))[:500],
                    "time": str(row.get("发布时间", "")),
                    "source": str(row.get("文章来源", "")),
                    "type": "news",
                })
    except Exception as e:
        logger.debug("获取公告失败 [%s]: %s", symbol, e)

    stock_data_cache.set(cache_key, docs, ttl=7200)
    return docs


def load_stock_research(symbol: str, limit: int = 10) -> List[Dict]:
    """获取个股研报摘要"""
    cache_key = f"rag:research:{symbol}"
    cached = stock_data_cache.get(cache_key)
    if cached is not None:
        return cached

    docs = []
    try:
        research_df = ak.stock_research_report_em(symbol=symbol)
        if research_df is not None and not research_df.empty:
            for _, row in research_df.head(limit).iterrows():
                docs.append({
                    "title": str(row.get("报告名称", "")),
                    "institution": str(row.get("机构", "")),
                    "date": str(row.get("日期", "")),
                    "type": "research",
                })
    except Exception as e:
        logger.debug("获取研报失败 [%s]: %s", symbol, e)

    stock_data_cache.set(cache_key, docs, ttl=7200)
    return docs
