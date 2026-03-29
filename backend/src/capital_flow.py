"""
资金流向分析模块
- 调用 AKShare stock_individual_fund_flow 获取主力/散户资金净流入
- 主力资金 = 超大单 + 大单净流入（机构/游资行为）
- 散户资金 = 中单 + 小单净流入
"""
import akshare as ak
import pandas as pd
from typing import Optional
from utils.cache import stock_data_cache


def get_capital_flow(symbol: str, days: int = 10) -> Optional[dict]:
    """
    获取个股近 N 日主力资金净流向（缓存 10 分钟）。

    :param symbol: 6位股票代码
    :param days: 取近多少个交易日（默认10）
    :return: 资金流向结果字典，获取失败返回 None
    """
    cache_key = f"capflow:{symbol}:{days}"
    cached = stock_data_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        market = "sh" if symbol.startswith("6") or symbol.startswith("9") else "sz"
        df = ak.stock_individual_fund_flow(stock=symbol, market=market)

        if df is None or df.empty:
            return None

        # 取近 N 日
        df = df.tail(days).copy()

        # 列名标准化（单位：元 → 万元）
        def col_to_wan(series: pd.Series) -> pd.Series:
            return (series / 10000).round(2)

        # 主力净流入（超大单 + 大单之和已在"主力净流入-净额"列中）
        main_col = "主力净流入-净额"
        super_col = "超大单净流入-净额"
        big_col = "大单净流入-净额"
        mid_col = "中单净流入-净额"
        small_col = "小单净流入-净额"

        df["main_net_wan"] = col_to_wan(df[main_col])
        df["retail_net_wan"] = col_to_wan(df[mid_col] + df[small_col])

        history = []
        for _, row in df.iterrows():
            history.append({
                "date": str(row["日期"]),
                "close": float(row["收盘价"]) if pd.notna(row["收盘价"]) else None,
                "change_pct": float(row["涨跌幅"]) if pd.notna(row["涨跌幅"]) else None,
                "main_net": float(row["main_net_wan"]),
                "retail_net": float(row["retail_net_wan"]),
            })

        # 汇总指标
        main_series = df["main_net_wan"]
        today_main = float(main_series.iloc[-1]) if len(main_series) >= 1 else 0.0
        five_day_main = float(main_series.iloc[-5:].sum()) if len(main_series) >= 5 else float(main_series.sum())
        ten_day_main = float(main_series.sum())

        # 趋势判断（最近5日主力流入方向）
        recent5 = main_series.iloc[-5:].tolist() if len(main_series) >= 5 else main_series.tolist()
        pos_days = sum(1 for x in recent5 if x > 0)
        neg_days = sum(1 for x in recent5 if x < 0)
        if pos_days >= 4:
            trend = "持续流入"
        elif neg_days >= 4:
            trend = "持续流出"
        elif pos_days > neg_days:
            trend = "偏流入"
        elif neg_days > pos_days:
            trend = "偏流出"
        else:
            trend = "震荡"

        # 今日主力 vs 散户博弈
        today_retail = float(df["retail_net_wan"].iloc[-1]) if len(df) >= 1 else 0.0
        if today_main > 0 and today_retail < 0:
            retail_vs_main = "主力流入、散户流出（分歧买入）"
        elif today_main < 0 and today_retail > 0:
            retail_vs_main = "主力流出、散户流入（分歧卖出）"
        elif today_main > 0 and today_retail > 0:
            retail_vs_main = "主力散户同步流入（共识买入）"
        elif today_main < 0 and today_retail < 0:
            retail_vs_main = "主力散户同步流出（共识卖出）"
        else:
            retail_vs_main = "资金流向中性"

        result = {
            "today_main_net": round(today_main, 2),
            "five_day_main_net": round(five_day_main, 2),
            "ten_day_main_net": round(ten_day_main, 2),
            "today_retail_net": round(today_retail, 2),
            "main_trend": trend,
            "retail_vs_main": retail_vs_main,
            "history": history,
        }
        stock_data_cache.set(cache_key, result, ttl=600)
        return result

    except Exception as e:
        # 资金流向获取失败不影响主流程
        return None
