"""
共享测试 fixtures
"""
import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timedelta


@pytest.fixture
def sample_ohlcv():
    """生成 120 天的模拟 OHLCV 数据"""
    np.random.seed(42)
    n = 120
    dates = pd.date_range(end=datetime.now(), periods=n, freq="B")

    # 模拟价格序列（随机游走）
    base_price = 10.0
    returns = np.random.normal(0.001, 0.02, n)
    prices = base_price * np.cumprod(1 + returns)

    df = pd.DataFrame({
        "open": prices * (1 + np.random.uniform(-0.01, 0.01, n)),
        "high": prices * (1 + np.abs(np.random.normal(0, 0.015, n))),
        "low": prices * (1 - np.abs(np.random.normal(0, 0.015, n))),
        "close": prices,
        "volume": np.random.randint(100000, 1000000, n).astype(float),
    }, index=dates)
    df.index.name = "date"

    # 确保 high >= close >= low
    df["high"] = df[["open", "close", "high"]].max(axis=1)
    df["low"] = df[["open", "close", "low"]].min(axis=1)

    return df


@pytest.fixture
def sample_ohlcv_short():
    """生成 20 天的短期数据（不足以计算所有指标）"""
    np.random.seed(123)
    n = 20
    dates = pd.date_range(end=datetime.now(), periods=n, freq="B")
    prices = 15.0 + np.cumsum(np.random.normal(0, 0.3, n))

    df = pd.DataFrame({
        "open": prices + np.random.uniform(-0.1, 0.1, n),
        "high": prices + np.abs(np.random.normal(0, 0.2, n)),
        "low": prices - np.abs(np.random.normal(0, 0.2, n)),
        "close": prices,
        "volume": np.random.randint(50000, 500000, n).astype(float),
    }, index=dates)
    df.index.name = "date"
    df["high"] = df[["open", "close", "high"]].max(axis=1)
    df["low"] = df[["open", "close", "low"]].min(axis=1)

    return df
