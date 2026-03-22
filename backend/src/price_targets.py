"""
价格目标计算模块
- 基于支撑/压力位分析给出三档（短/中/长线）价格目标
- 支撑位来源：局部低点（swing lows）+ 动态均线 + 斐波那契回调
- 压力位来源：局部高点（swing highs）+ 布林带上轨 + 历史成交密集区
"""
import pandas as pd
import numpy as np
from typing import Optional


def find_swing_lows(prices: pd.Series, window: int = 5) -> list[float]:
    """识别局部低点：左右各 window 根K线内均比它高"""
    lows = []
    arr = prices.values
    for i in range(window, len(arr) - window):
        segment = arr[i - window: i + window + 1]
        if arr[i] == segment.min() and list(segment).count(arr[i]) == 1:
            lows.append(float(round(arr[i], 2)))
    return sorted(set(lows))


def find_swing_highs(prices: pd.Series, window: int = 5) -> list[float]:
    """识别局部高点：左右各 window 根K线内均比它低"""
    highs = []
    arr = prices.values
    for i in range(window, len(arr) - window):
        segment = arr[i - window: i + window + 1]
        if arr[i] == segment.max() and list(segment).count(arr[i]) == 1:
            highs.append(float(round(arr[i], 2)))
    return sorted(set(highs), reverse=True)


def find_fibonacci_levels(high: float, low: float) -> list[float]:
    """斐波那契回调位（从高到低排列：0.236 → 0.786）"""
    diff = high - low
    return [round(high - diff * r, 2) for r in (0.236, 0.382, 0.500, 0.618, 0.786)]


def _nearest_supports(current: float, supports: list[float], n: int = 3) -> list[float]:
    """取当前价以下最近的 n 个支撑位"""
    below = [s for s in supports if s < current * 0.999]
    return sorted(below, reverse=True)[:n]


def _nearest_resistances(current: float, resistances: list[float], n: int = 3) -> list[float]:
    """取当前价以上最近的 n 个压力位"""
    above = [r for r in resistances if r > current * 1.001]
    return sorted(above)[:n]


def _compute_timeframe(
    current_price: float,
    supports: list[float],
    resistances: list[float],
    horizon: str,
    basis: str,
) -> dict:
    """
    根据支撑/压力位生成单档价格目标
    买入区间 = 最近支撑 ± 小幅缓冲
    止损    = 买入区下沿再下 3%
    目标价  = 最近三个压力位（不足则外推）
    盈亏比  = (target_1 - buy_mid) / (buy_mid - stop_loss)
    """
    # 支撑位（买入区间）
    near_supports = _nearest_supports(current_price, supports, 2)
    if near_supports:
        buy_low = round(near_supports[-1] * 0.98, 2)   # 第二支撑再下 2%
        buy_high = round(near_supports[0] * 1.01, 2)   # 最近支撑上方 1%
        buy_high = min(buy_high, current_price)          # 不超过当前价
    else:
        # 无明显支撑，用当前价下 3%~5%
        buy_low = round(current_price * 0.95, 2)
        buy_high = round(current_price * 0.97, 2)

    buy_mid = round((buy_low + buy_high) / 2, 2)
    stop_loss = round(buy_low * 0.97, 2)  # 买入下沿再下 3%

    # 目标价（压力位）
    near_resistances = _nearest_resistances(current_price, resistances, 3)
    while len(near_resistances) < 3:
        # 不足三个则外推（每次 +5%）
        last = near_resistances[-1] if near_resistances else current_price
        near_resistances.append(round(last * 1.05, 2))
    targets = [round(t, 2) for t in near_resistances[:3]]

    # 盈亏比
    if buy_mid > stop_loss:
        risk = buy_mid - stop_loss
        reward = targets[0] - buy_mid
        risk_reward = round(reward / risk, 1) if risk > 0 else 1.0
    else:
        risk_reward = 1.0

    # 潜在收益（以中间买入价到第一目标）
    potential_pct = round((targets[0] - buy_mid) / buy_mid * 100, 1) if buy_mid > 0 else 0

    return {
        "buy_zone": [buy_low, buy_high],
        "stop_loss": stop_loss,
        "targets": targets,
        "risk_reward": risk_reward,
        "potential_pct": potential_pct,
        "horizon": horizon,
        "basis": basis,
    }


def calculate_price_targets(df: pd.DataFrame, current_price: float) -> dict:
    """
    基于历史 OHLCV 数据计算三档价格目标。

    :param df: 含 open/high/low/close/volume/ma5/ma10/ma20/ma60/bb_upper/bb_lower 的 DataFrame
    :param current_price: 最新收盘价
    :return: { current_price, short_term, medium_term, long_term }
    """
    if df is None or len(df) < 10:
        return _fallback_targets(current_price)

    close = df["close"]
    high = df["high"]
    low = df["low"]

    # ── 短线（最近20日）──────────────────────────────────────
    short_df = df.tail(20)
    short_lows   = find_swing_lows(short_df["low"], window=3)
    short_highs  = find_swing_highs(short_df["high"], window=3)

    # 加入均线支撑
    if "ma5" in df.columns and df["ma5"].iloc[-1] is not None:
        short_lows.append(round(float(df["ma5"].iloc[-1]), 2))
    if "ma10" in df.columns and df["ma10"].iloc[-1] is not None:
        short_lows.append(round(float(df["ma10"].iloc[-1]), 2))
    # 加入布林下轨
    if "bb_lower" in df.columns and df["bb_lower"].iloc[-1] is not None:
        short_lows.append(round(float(df["bb_lower"].iloc[-1]), 2))
    # 加入布林上轨作压力
    if "bb_upper" in df.columns and df["bb_upper"].iloc[-1] is not None:
        short_highs.append(round(float(df["bb_upper"].iloc[-1]), 2))

    short_lows = sorted(set(short_lows))
    short_highs = sorted(set(short_highs), reverse=True)

    short_basis_parts = []
    if "ma10" in df.columns:
        short_basis_parts.append("MA10支撑")
    if "bb_lower" in df.columns:
        short_basis_parts.append("布林下轨")
    short_basis = "+".join(short_basis_parts) or "近期低点"

    short_term = _compute_timeframe(
        current_price, short_lows, short_highs,
        horizon="1-2周", basis=short_basis
    )

    # ── 中线（最近60日）──────────────────────────────────────
    mid_df = df.tail(60)
    mid_lows  = find_swing_lows(mid_df["low"], window=4)
    mid_highs = find_swing_highs(mid_df["high"], window=4)

    if "ma20" in df.columns and df["ma20"].iloc[-1] is not None:
        mid_lows.append(round(float(df["ma20"].iloc[-1]), 2))
    if "ma60" in df.columns and df["ma60"].iloc[-1] is not None:
        mid_lows.append(round(float(df["ma60"].iloc[-1]), 2))

    # 斐波那契（中线用60日高低点）
    hi60 = float(mid_df["high"].max())
    lo60 = float(mid_df["low"].min())
    fib_levels = find_fibonacci_levels(hi60, lo60)
    for fib in fib_levels:
        if fib < current_price:
            mid_lows.append(fib)
        else:
            mid_highs.append(fib)

    mid_lows  = sorted(set(round(v, 2) for v in mid_lows))
    mid_highs = sorted(set(round(v, 2) for v in mid_highs), reverse=True)

    mid_basis_parts = []
    if "ma20" in df.columns:
        mid_basis_parts.append("MA20支撑")
    if "ma60" in df.columns:
        mid_basis_parts.append("MA60支撑")
    mid_basis_parts.append("斐波那契回调")
    mid_basis = "+".join(mid_basis_parts)

    medium_term = _compute_timeframe(
        current_price, mid_lows, mid_highs,
        horizon="1-3月", basis=mid_basis
    )

    # ── 长线（全量数据）──────────────────────────────────────
    long_lows  = find_swing_lows(low, window=5)
    long_highs = find_swing_highs(high, window=5)

    if "ma60" in df.columns and df["ma60"].iloc[-1] is not None:
        long_lows.append(round(float(df["ma60"].iloc[-1]), 2))

    # 斐波那契（全周期）
    hi_all = float(high.max())
    lo_all = float(low.min())
    fib_all = find_fibonacci_levels(hi_all, lo_all)
    for fib in fib_all:
        if fib < current_price:
            long_lows.append(fib)
        else:
            long_highs.append(fib)

    long_lows  = sorted(set(round(v, 2) for v in long_lows))
    long_highs = sorted(set(round(v, 2) for v in long_highs), reverse=True)

    long_term = _compute_timeframe(
        current_price, long_lows, long_highs,
        horizon="6-12月", basis="MA60+历史低点+斐波那契长线支撑"
    )

    return {
        "current_price": current_price,
        "short_term": short_term,
        "medium_term": medium_term,
        "long_term": long_term,
    }


def _fallback_targets(current_price: float) -> dict:
    """数据不足时的降级输出（固定百分比）"""
    def make(pct_buy, pct_sl, pct_t1, pct_t2, pct_t3, horizon):
        buy_low  = round(current_price * (1 - pct_buy - 0.02), 2)
        buy_high = round(current_price * (1 - pct_buy + 0.01), 2)
        sl       = round(buy_low * 0.97, 2)
        t1       = round(current_price * (1 + pct_t1), 2)
        t2       = round(current_price * (1 + pct_t2), 2)
        t3       = round(current_price * (1 + pct_t3), 2)
        return {
            "buy_zone": [buy_low, buy_high],
            "stop_loss": sl,
            "targets": [t1, t2, t3],
            "risk_reward": round(pct_t1 / (pct_buy + 0.03), 1),
            "potential_pct": round(pct_t1 * 100, 1),
            "horizon": horizon,
            "basis": "固定比例估算（数据不足）",
        }
    return {
        "current_price": current_price,
        "short_term":  make(0.03, 0.05, 0.05, 0.10, 0.15, "1-2周"),
        "medium_term": make(0.05, 0.08, 0.10, 0.18, 0.25, "1-3月"),
        "long_term":   make(0.08, 0.12, 0.20, 0.35, 0.50, "6-12月"),
    }
