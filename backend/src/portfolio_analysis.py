"""
多股票组合分析
- 计算相关性矩阵
- 组合收益对比
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict
from data.provider_factory import get_history_with_fallback
from datetime import datetime

logger = logging.getLogger(__name__)


def analyze_portfolio(symbols: List[str]) -> Dict:
    """
    分析多只股票的组合特性。
    :param symbols: 股票代码列表（最多 10 只）
    :return: 包含相关性矩阵、收益对比等的分析结果
    """
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = "20240101"

    close_data = {}
    stock_info = {}

    for symbol in symbols:
        try:
            df, source = get_history_with_fallback(symbol, start_date, end_date)
            if df is not None and not df.empty and "close" in df.columns:
                close_data[symbol] = df["close"]
                stock_info[symbol] = {
                    "latest_price": round(float(df["close"].iloc[-1]), 2),
                    "total_return": round(
                        (float(df["close"].iloc[-1]) - float(df["close"].iloc[0]))
                        / float(df["close"].iloc[0]) * 100, 2
                    ),
                }
        except Exception as e:
            logger.warning("获取 %s 数据失败: %s", symbol, e)
            stock_info[symbol] = {"error": str(e)}

    if len(close_data) < 2:
        return {
            "error": "需要至少2只股票才能进行组合分析",
            "stock_info": stock_info,
        }

    # 对齐日期
    combined = pd.DataFrame(close_data)
    combined = combined.dropna()

    if len(combined) < 20:
        return {
            "error": "有效重叠数据不足20天",
            "stock_info": stock_info,
        }

    # 日收益率
    returns = combined.pct_change().dropna()

    # 相关性矩阵
    corr_matrix = returns.corr()
    correlation = {}
    for s1 in corr_matrix.columns:
        correlation[s1] = {}
        for s2 in corr_matrix.columns:
            correlation[s1][s2] = round(float(corr_matrix.loc[s1, s2]), 4)

    # 各股票统计
    stats = {}
    for sym in returns.columns:
        daily_ret = returns[sym]
        stats[sym] = {
            "annualized_return": round(float(daily_ret.mean() * 252 * 100), 2),
            "annualized_volatility": round(float(daily_ret.std() * np.sqrt(252) * 100), 2),
            "sharpe_ratio": round(
                float(daily_ret.mean() / daily_ret.std() * np.sqrt(252))
                if daily_ret.std() > 0 else 0, 4
            ),
            "max_drawdown": round(_max_drawdown(combined[sym]) * 100, 2),
        }

    # 等权组合表现
    equal_weight_returns = returns.mean(axis=1)
    eq_cum = (1 + equal_weight_returns).cumprod()

    equal_weight_stats = {
        "annualized_return": round(float(equal_weight_returns.mean() * 252 * 100), 2),
        "annualized_volatility": round(float(equal_weight_returns.std() * np.sqrt(252) * 100), 2),
        "sharpe_ratio": round(
            float(equal_weight_returns.mean() / equal_weight_returns.std() * np.sqrt(252))
            if equal_weight_returns.std() > 0 else 0, 4
        ),
        "total_return": round(float((eq_cum.iloc[-1] - 1) * 100), 2),
    }

    # 收益曲线数据（归一化到100）
    normalized = (combined / combined.iloc[0] * 100).reset_index()
    normalized["date"] = normalized["date"].dt.strftime("%Y-%m-%d")
    return_curves = normalized.to_dict("records")

    return {
        "symbols": symbols,
        "stock_info": stock_info,
        "correlation": correlation,
        "individual_stats": stats,
        "equal_weight_portfolio": equal_weight_stats,
        "return_curves": return_curves,
    }


def _max_drawdown(prices: pd.Series) -> float:
    peak = prices.expanding(min_periods=1).max()
    dd = (prices - peak) / peak
    return float(abs(dd.min()))
