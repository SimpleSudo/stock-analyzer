"""
宏观经济数据获取
- Shibor 利率
- 北向资金
- 上证指数趋势
"""
import logging
import akshare as ak
import pandas as pd
from typing import Dict, Optional
from utils.cache import stock_data_cache

logger = logging.getLogger(__name__)


def get_macro_indicators() -> Dict:
    """获取宏观经济指标（缓存 30 分钟）"""
    cache_key = "macro:indicators"
    cached = stock_data_cache.get(cache_key)
    if cached is not None:
        return cached

    result: Dict = {}

    # Shibor 隔夜利率
    try:
        shibor_df = ak.rate_interbank(market="上海银行同业拆借市场", symbol="Shibor人民币", indicator="隔夜")
        if shibor_df is not None and not shibor_df.empty:
            latest = shibor_df.iloc[-1]
            result["shibor_overnight"] = round(float(latest.iloc[-1]), 4)
    except Exception as e:
        logger.debug("Shibor 获取失败: %s", e)

    # 北向资金（沪深港通）
    try:
        north_df = ak.stock_hsgt_north_net_flow_in_em(symbol="北上")
        if north_df is not None and not north_df.empty:
            recent = north_df.tail(5)
            today_flow = float(recent.iloc[-1]["当日净买入"])
            five_day_flow = float(recent["当日净买入"].sum())
            result["north_today"] = round(today_flow / 1e8, 2)  # 亿元
            result["north_5day"] = round(five_day_flow / 1e8, 2)
            pos_days = sum(1 for x in recent["当日净买入"] if float(x) > 0)
            result["north_trend"] = "持续流入" if pos_days >= 4 else "持续流出" if pos_days <= 1 else "震荡"
    except Exception as e:
        logger.debug("北向资金获取失败: %s", e)

    # 上证指数趋势
    try:
        sh_df = ak.stock_zh_index_daily(symbol="sh000001")
        if sh_df is not None and not sh_df.empty:
            sh_df = sh_df.tail(60)
            close = sh_df["close"]
            ma20 = close.rolling(20).mean().iloc[-1]
            ma60 = close.rolling(60).mean().iloc[-1] if len(close) >= 60 else None
            latest_close = float(close.iloc[-1])
            result["sh_index"] = round(latest_close, 2)
            result["sh_above_ma20"] = latest_close > ma20
            if ma60:
                result["sh_above_ma60"] = latest_close > ma60
            result["sh_trend"] = "上涨趋势" if latest_close > ma20 else "下跌趋势"
    except Exception as e:
        logger.debug("上证指数获取失败: %s", e)

    stock_data_cache.set(cache_key, result, ttl=1800)
    return result
