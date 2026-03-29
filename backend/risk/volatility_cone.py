"""波动率锥 - 多时间窗口波动率分位数"""
import numpy as np
import pandas as pd
from typing import Dict, List


def calculate_volatility_cone(
    returns: pd.Series,
    windows: list = None,
) -> Dict[str, Dict]:
    """
    计算波动率锥
    :param returns: 日收益率序列
    :param windows: 时间窗口列表（天）
    :return: {window: {current, p10, p25, p50, p75, p90}}
    """
    if windows is None:
        windows = [5, 10, 20, 60, 120]

    result = {}
    for w in windows:
        if len(returns) < w + 10:
            continue
        rolling_vol = returns.rolling(w).std() * np.sqrt(252)
        rolling_vol = rolling_vol.dropna()
        if len(rolling_vol) < 5:
            continue
        result[f"{w}d"] = {
            "current": round(float(rolling_vol.iloc[-1]) * 100, 2),
            "p10": round(float(np.percentile(rolling_vol, 10)) * 100, 2),
            "p25": round(float(np.percentile(rolling_vol, 25)) * 100, 2),
            "p50": round(float(np.percentile(rolling_vol, 50)) * 100, 2),
            "p75": round(float(np.percentile(rolling_vol, 75)) * 100, 2),
            "p90": round(float(np.percentile(rolling_vol, 90)) * 100, 2),
        }
    return result
