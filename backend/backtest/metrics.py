"""
Backtest metrics calculation utilities
"""
import numpy as np
import pandas as pd
from typing import List, Dict

def calculate_returns(portfolio_values: List[float]) -> List[float]:
    """Calculate period returns from portfolio values"""
    if len(portfolio_values) < 2:
        return []
    returns = []
    for i in range(1, len(portfolio_values)):
        ret = (portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]
        returns.append(ret)
    return returns

def calculate_sharpe_ratio(returns: List[float], risk_free: float = 0.0, periods_per_year: int = 252) -> float:
    """Calculate annualized Sharpe ratio"""
    if len(returns) < 2:
        return 0.0
    returns_array = np.array(returns)
    excess_returns = returns_array - risk_free / periods_per_year
    if np.std(excess_returns) == 0:
        return 0.0
    return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(periods_per_year)

def calculate_max_drawdown(portfolio_values: List[float]) -> float:
    """Calculate maximum drawdown"""
    if len(portfolio_values) == 0:
        return 0.0
    peak = portfolio_values[0]
    max_dd = 0.0
    for val in portfolio_values:
        if val > peak:
            peak = val
        dd = (peak - val) / peak
        if dd > max_dd:
            max_dd = dd
    return max_dd

def calculate_win_rate(trades: List[Dict]) -> float:
    """Calculate win rate from trades list"""
    if not trades:
        return 0.0
    wins = 0
    total = 0
    # Simple pairing: assume trades are alternating buy/sell
    # More realistic would need to track positions
    for trade in trades:
        if trade.get('action') == 'SELL':
            total += 1
            if trade.get('profit', 0) > 0:
                wins += 1
    return wins / total if total > 0 else 0.0
