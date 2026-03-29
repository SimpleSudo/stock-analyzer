"""
因子库 - 定义各类 Alpha 因子
每个因子函数接收 DataFrame，返回 Series（因子值）
"""
import numpy as np
import pandas as pd


# ── 动量因子 ────────────────────────────────────────────

def momentum_5d(df: pd.DataFrame) -> pd.Series:
    return df["close"].pct_change(5)

def momentum_20d(df: pd.DataFrame) -> pd.Series:
    return df["close"].pct_change(20)

def momentum_60d(df: pd.DataFrame) -> pd.Series:
    return df["close"].pct_change(60)


# ── 均值回归因子 ────────────────────────────────────────

def rsi_factor(df: pd.DataFrame) -> pd.Series:
    """RSI 均值回归：RSI 越低越看多"""
    if "rsi" in df.columns:
        return 50 - df["rsi"]  # 正值=超卖看多
    return pd.Series(0, index=df.index)

def bb_position(df: pd.DataFrame) -> pd.Series:
    """布林带位置：越接近下轨越看多"""
    if all(c in df.columns for c in ["bb_upper", "bb_lower", "close"]):
        width = df["bb_upper"] - df["bb_lower"]
        width = width.replace(0, np.nan)
        return (df["bb_upper"] - df["close"]) / width  # 1=下轨, 0=上轨
    return pd.Series(0.5, index=df.index)


# ── 波动率因子 ──────────────────────────────────────────

def volatility_20d(df: pd.DataFrame) -> pd.Series:
    return df["close"].pct_change().rolling(20).std() * np.sqrt(252)

def atr_ratio(df: pd.DataFrame) -> pd.Series:
    """ATR 占价格比例"""
    if "atr" in df.columns:
        return df["atr"] / df["close"]
    return pd.Series(0, index=df.index)


# ── 成交量因子 ──────────────────────────────────────────

def volume_ratio(df: pd.DataFrame) -> pd.Series:
    """量比：当日成交量 / 5 日均量"""
    ma5_vol = df["volume"].rolling(5).mean()
    return df["volume"] / ma5_vol.replace(0, np.nan)

def obv_slope(df: pd.DataFrame) -> pd.Series:
    """OBV 5 日斜率"""
    if "obv" in df.columns:
        return df["obv"].diff(5)
    return pd.Series(0, index=df.index)


# ── 趋势因子 ────────────────────────────────────────────

def ma_alignment(df: pd.DataFrame) -> pd.Series:
    """均线多头排列分数 (MA5 > MA10 > MA20 > MA60 = +1 each)"""
    score = pd.Series(0, index=df.index, dtype=float)
    for short, long in [("ma5", "ma10"), ("ma10", "ma20"), ("ma20", "ma60")]:
        if short in df.columns and long in df.columns:
            score += (df[short] > df[long]).astype(float)
    return score


# ── 因子注册表 ──────────────────────────────────────────

FACTOR_REGISTRY = {
    "momentum_5d": {"fn": momentum_5d, "category": "动量"},
    "momentum_20d": {"fn": momentum_20d, "category": "动量"},
    "momentum_60d": {"fn": momentum_60d, "category": "动量"},
    "rsi_factor": {"fn": rsi_factor, "category": "均值回归"},
    "bb_position": {"fn": bb_position, "category": "均值回归"},
    "volatility_20d": {"fn": volatility_20d, "category": "波动率"},
    "atr_ratio": {"fn": atr_ratio, "category": "波动率"},
    "volume_ratio": {"fn": volume_ratio, "category": "成交量"},
    "obv_slope": {"fn": obv_slope, "category": "成交量"},
    "ma_alignment": {"fn": ma_alignment, "category": "趋势"},
}
