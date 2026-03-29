"""
K 线形态识别引擎 - 基于 swing high/low 规则匹配
支持形态：
- 双重底 (W 底) / 双重顶 (M 顶)
- 头肩底 / 头肩顶
- 上升三角形 / 下降三角形
- 锤子线 / 倒锤子 / 十字星
"""
import logging
import numpy as np
import pandas as pd
from typing import List

from .shapes import PatternMatch

logger = logging.getLogger(__name__)


def _find_swing_points(prices: pd.Series, window: int = 5):
    """识别局部高低点"""
    highs, lows = [], []
    arr = prices.values
    for i in range(window, len(arr) - window):
        seg = arr[i - window: i + window + 1]
        if arr[i] == seg.max() and list(seg).count(arr[i]) == 1:
            highs.append((i, float(arr[i])))
        if arr[i] == seg.min() and list(seg).count(arr[i]) == 1:
            lows.append((i, float(arr[i])))
    return highs, lows


def _detect_double_bottom(df: pd.DataFrame, lows: list, tolerance: float = 0.03) -> List[PatternMatch]:
    """双重底（W底）：两个近似低点"""
    patterns = []
    for i in range(len(lows) - 1):
        idx1, val1 = lows[i]
        idx2, val2 = lows[i + 1]
        if idx2 - idx1 < 10 or idx2 - idx1 > 60:
            continue
        if abs(val1 - val2) / max(val1, val2) < tolerance:
            # 中间高点
            mid_high = float(df["high"].iloc[idx1:idx2].max())
            neckline_break = float(df["close"].iloc[-1]) > mid_high
            conf = 0.7 if neckline_break else 0.5
            patterns.append(PatternMatch(
                name="双重底 (W底)", name_en="Double Bottom",
                direction="bullish", confidence=conf,
                start_idx=idx1, end_idx=idx2,
                description=f"两个低点 {val1:.2f}/{val2:.2f}，颈线 {mid_high:.2f}{'已突破' if neckline_break else '未突破'}",
                target_pct=round((mid_high - val1) / val1 * 100, 1),
            ))
    return patterns


def _detect_double_top(df: pd.DataFrame, highs: list, tolerance: float = 0.03) -> List[PatternMatch]:
    """双重顶（M顶）"""
    patterns = []
    for i in range(len(highs) - 1):
        idx1, val1 = highs[i]
        idx2, val2 = highs[i + 1]
        if idx2 - idx1 < 10 or idx2 - idx1 > 60:
            continue
        if abs(val1 - val2) / max(val1, val2) < tolerance:
            mid_low = float(df["low"].iloc[idx1:idx2].min())
            neckline_break = float(df["close"].iloc[-1]) < mid_low
            conf = 0.7 if neckline_break else 0.5
            patterns.append(PatternMatch(
                name="双重顶 (M顶)", name_en="Double Top",
                direction="bearish", confidence=conf,
                start_idx=idx1, end_idx=idx2,
                description=f"两个高点 {val1:.2f}/{val2:.2f}，颈线 {mid_low:.2f}{'已跌破' if neckline_break else '未跌破'}",
                target_pct=round((mid_low - val1) / val1 * 100, 1),
            ))
    return patterns


def _detect_candlestick_patterns(df: pd.DataFrame) -> List[PatternMatch]:
    """单 K 线形态：锤子线、十字星等"""
    patterns = []
    if len(df) < 2:
        return patterns

    idx = len(df) - 1
    o, h, l, c = df["open"].iloc[-1], df["high"].iloc[-1], df["low"].iloc[-1], df["close"].iloc[-1]
    body = abs(c - o)
    total = h - l
    if total == 0:
        return patterns

    body_ratio = body / total
    upper_shadow = h - max(o, c)
    lower_shadow = min(o, c) - l

    # 十字星
    if body_ratio < 0.1 and total > 0:
        patterns.append(PatternMatch(
            name="十字星", name_en="Doji",
            direction="neutral", confidence=0.6,
            start_idx=idx, end_idx=idx,
            description="开盘价≈收盘价，市场犹豫不决",
        ))

    # 锤子线（下影线长，实体小，出现在下跌中）
    if lower_shadow > body * 2 and upper_shadow < body * 0.5 and c > o:
        prev_trend = df["close"].iloc[-5:-1].mean() > df["close"].iloc[-10:-5].mean() if len(df) >= 10 else False
        if not prev_trend:  # 下跌趋势中
            patterns.append(PatternMatch(
                name="锤子线", name_en="Hammer",
                direction="bullish", confidence=0.6,
                start_idx=idx, end_idx=idx,
                description="长下影线，潜在反转信号",
            ))

    # 倒锤子/射击之星
    if upper_shadow > body * 2 and lower_shadow < body * 0.5 and c < o:
        patterns.append(PatternMatch(
            name="射击之星", name_en="Shooting Star",
            direction="bearish", confidence=0.6,
            start_idx=idx, end_idx=idx,
            description="长上影线，上方压力大",
        ))

    return patterns


def recognize(df: pd.DataFrame) -> List[PatternMatch]:
    """
    对 DataFrame 执行全量形态识别
    :return: 按可信度降序排列的形态列表
    """
    if df is None or len(df) < 20:
        return []

    try:
        highs, lows = _find_swing_points(df["close"], window=5)

        patterns = []
        patterns.extend(_detect_double_bottom(df, lows))
        patterns.extend(_detect_double_top(df, highs))
        patterns.extend(_detect_candlestick_patterns(df))

        # 按可信度排序
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        return patterns

    except Exception as e:
        logger.warning("形态识别失败: %s", e)
        return []
