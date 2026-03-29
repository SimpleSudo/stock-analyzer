"""
VaR（在险价值）计算器
- 历史模拟法 VaR
- 蒙特卡洛 VaR
"""
import numpy as np
import pandas as pd
from typing import Dict


def calculate_historical_var(
    returns: pd.Series, confidence_levels: list = None, holding_period: int = 1
) -> Dict[str, float]:
    """
    历史模拟法 VaR
    :param returns: 日收益率序列
    :param confidence_levels: 置信水平列表，如 [0.95, 0.99]
    :param holding_period: 持有期（天）
    """
    if confidence_levels is None:
        confidence_levels = [0.95, 0.99]
    if len(returns) < 20:
        return {f"VaR_{int(cl*100)}%": None for cl in confidence_levels}

    result = {}
    for cl in confidence_levels:
        var = float(np.percentile(returns, (1 - cl) * 100))
        # 调整持有期（根号T法则）
        var_adjusted = var * np.sqrt(holding_period)
        result[f"VaR_{int(cl*100)}%"] = round(var_adjusted * 100, 2)  # 百分比
    return result


def calculate_monte_carlo_var(
    returns: pd.Series,
    confidence_levels: list = None,
    simulations: int = 10000,
    holding_period: int = 5,
) -> Dict[str, float]:
    """蒙特卡洛 VaR"""
    if confidence_levels is None:
        confidence_levels = [0.95, 0.99]
    if len(returns) < 20:
        return {f"MC_VaR_{int(cl*100)}%": None for cl in confidence_levels}

    mu = returns.mean()
    sigma = returns.std()
    simulated = np.random.normal(mu, sigma, (simulations, holding_period))
    portfolio_returns = simulated.sum(axis=1)

    result = {}
    for cl in confidence_levels:
        var = float(np.percentile(portfolio_returns, (1 - cl) * 100))
        result[f"MC_VaR_{int(cl*100)}%_{holding_period}d"] = round(var * 100, 2)
    return result
