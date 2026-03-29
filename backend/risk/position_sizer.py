"""仓位管理建议 - Kelly 公式 + ATR 方法"""
import numpy as np
import pandas as pd
from typing import Dict


def kelly_position(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """
    Kelly 公式计算最优仓位比例
    :return: 0~1 之间的仓位比例（经半Kelly保守处理）
    """
    if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
        return 0.0
    b = avg_win / abs(avg_loss)  # 赔率
    kelly = (win_rate * b - (1 - win_rate)) / b
    # 半 Kelly（更保守）
    half_kelly = max(0, min(kelly / 2, 0.5))
    return round(half_kelly, 4)


def atr_position(
    capital: float,
    current_price: float,
    atr: float,
    risk_pct: float = 0.02,
) -> Dict:
    """
    ATR 仓位法：每笔交易最多亏损总资金的 risk_pct
    :param capital: 总资金
    :param current_price: 当前价
    :param atr: 14 日 ATR
    :param risk_pct: 单笔最大风险比例（默认 2%）
    :return: {shares, position_pct, stop_loss}
    """
    if atr <= 0 or current_price <= 0:
        return {"shares": 0, "position_pct": 0, "stop_loss": 0}

    risk_amount = capital * risk_pct
    stop_distance = atr * 2  # 2 倍 ATR 止损
    shares = int(risk_amount / stop_distance)
    # A 股整手
    shares = (shares // 100) * 100
    position_value = shares * current_price
    position_pct = position_value / capital if capital > 0 else 0

    return {
        "shares": shares,
        "position_pct": round(position_pct * 100, 1),
        "position_value": round(position_value, 2),
        "stop_loss": round(current_price - stop_distance, 2),
        "stop_distance": round(stop_distance, 2),
        "risk_amount": round(risk_amount, 2),
    }


def calculate_risk_metrics(df: pd.DataFrame, capital: float = 100000) -> Dict:
    """
    综合风险指标计算
    :param df: 含 close, atr 列的 DataFrame
    :param capital: 总资金
    """
    from risk.var_calculator import calculate_historical_var, calculate_monte_carlo_var
    from risk.volatility_cone import calculate_volatility_cone

    returns = df["close"].pct_change().dropna()

    result = {
        "var": calculate_historical_var(returns),
        "mc_var": calculate_monte_carlo_var(returns),
        "volatility_cone": calculate_volatility_cone(returns),
    }

    # ATR 仓位建议
    if "atr" in df.columns and pd.notna(df["atr"].iloc[-1]):
        current_price = float(df["close"].iloc[-1])
        atr_val = float(df["atr"].iloc[-1])
        result["position"] = atr_position(capital, current_price, atr_val)

    # 年化波动率
    if len(returns) >= 20:
        annual_vol = float(returns.std() * np.sqrt(252))
        result["annual_volatility"] = round(annual_vol * 100, 2)

    return result
