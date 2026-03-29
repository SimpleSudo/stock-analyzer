"""
回测引擎 - 基于技术指标信号的策略回测
- 使用滚动窗口分析，消除前瞻偏差
- 支持手续费和滑点模拟
- 配对交易计算盈亏和胜率
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.provider_factory import get_history_with_fallback
from backtest.metrics import calculate_sharpe_ratio, calculate_max_drawdown

logger = logging.getLogger(__name__)


class BacktestEngine:
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.0003,
        slippage: float = 0.001,
    ):
        """
        初始化回测引擎。
        :param initial_capital: 初始资金
        :param commission: 手续费率（单边）
        :param slippage: 滑点率
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

    # ── 数据获取 ──────────────────────────────────────────

    def fetch_historical_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """获取历史日线数据（使用 provider_factory 的故障转移机制）"""
        try:
            df, _ = get_history_with_fallback(symbol, start_date, end_date)
            return df
        except Exception as e:
            logger.error("获取历史数据失败 [%s]: %s", symbol, e)
            return pd.DataFrame()

    # ── 滚动窗口信号生成（消除前瞻偏差）──────────────────

    @staticmethod
    def _rolling_signal(historical_slice: pd.DataFrame) -> str:
        """
        基于截至当日的历史数据生成交易信号。
        仅使用 MA 交叉 + RSI + MACD，不使用未来数据。
        使用独立副本避免 ewm 状态泄漏。
        """
        if len(historical_slice) < 60:
            return "HOLD"

        close = historical_slice["close"].copy()

        # MA 交叉
        ma5 = close.rolling(5).mean()
        ma10 = close.rolling(10).mean()
        ma20 = close.rolling(20).mean()

        ma5_now, ma5_prev = ma5.iloc[-1], ma5.iloc[-2]
        ma10_now, ma10_prev = ma10.iloc[-1], ma10.iloc[-2]

        score = 0

        # MA5/MA10 金叉/死叉
        if ma5_now > ma10_now and ma5_prev <= ma10_prev:
            score += 2
        elif ma5_now < ma10_now and ma5_prev >= ma10_prev:
            score -= 2

        # RSI
        delta = close.diff()
        up = delta.clip(lower=0).rolling(14).mean()
        down = (-delta.clip(upper=0)).rolling(14).mean()
        rs = up.iloc[-1] / down.iloc[-1] if down.iloc[-1] != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if rs != 0 else 50

        if rsi < 30:
            score += 2
        elif rsi > 70:
            score -= 2

        # MACD
        exp12 = close.ewm(span=12, adjust=False).mean()
        exp26 = close.ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal_line = macd.ewm(span=9, adjust=False).mean()

        if macd.iloc[-1] > signal_line.iloc[-1] and macd.iloc[-2] <= signal_line.iloc[-2]:
            score += 2
        elif macd.iloc[-1] < signal_line.iloc[-1] and macd.iloc[-2] >= signal_line.iloc[-2]:
            score -= 2

        # 趋势
        ma60 = close.rolling(60).mean()
        if pd.notna(ma60.iloc[-1]) and close.iloc[-1] > ma60.iloc[-1]:
            score += 1
        elif pd.notna(ma60.iloc[-1]):
            score -= 1

        if score >= 3:
            return "BUY"
        elif score <= -3:
            return "SELL"
        return "HOLD"

    # ── 回测主流程 ────────────────────────────────────────

    def run_backtest(self, symbol: str, start_date: str, end_date: str) -> Dict:
        """
        对指定股票在给定日期范围内进行回测。
        :return: 回测结果字典
        """
        df = self.fetch_historical_data(symbol, start_date, end_date)
        if df.empty:
            return {"error": "无法获取历史数据"}

        cash = self.initial_capital
        shares = 0
        portfolio_history: List[Dict] = []
        trades: List[Dict] = []
        last_buy_price: Optional[float] = None

        dates = df.index
        for i in range(len(dates) - 1):
            current_date = dates[i]
            next_date = dates[i + 1]

            # 滚动窗口：仅使用截至当前日期的数据
            historical_slice = df.loc[:current_date]
            signal = self._rolling_signal(historical_slice)

            open_price = df.loc[next_date, "open"]

            if signal == "BUY" and shares == 0:
                price = open_price * (1 + self.slippage)
                max_shares = int(cash // (price * (1 + self.commission)))
                # A 股买入按 100 股整手
                max_shares = (max_shares // 100) * 100
                if max_shares > 0:
                    cost = max_shares * price * (1 + self.commission)
                    shares = max_shares
                    cash -= cost
                    last_buy_price = price
                    trades.append({
                        "date": next_date.strftime("%Y-%m-%d"),
                        "action": "BUY",
                        "shares": max_shares,
                        "price": round(price, 4),
                        "cost": round(cost, 2),
                    })

            elif signal == "SELL" and shares > 0:
                price = open_price * (1 - self.slippage)
                revenue = shares * price * (1 - self.commission)
                profit = revenue - (last_buy_price or price) * shares * (1 + self.commission)
                trades.append({
                    "date": next_date.strftime("%Y-%m-%d"),
                    "action": "SELL",
                    "shares": shares,
                    "price": round(price, 4),
                    "revenue": round(revenue, 2),
                    "profit": round(profit, 2),
                })
                cash += revenue
                shares = 0
                last_buy_price = None

            # 每日市值记录
            close_price = df.loc[current_date, "close"]
            total_value = cash + shares * close_price
            portfolio_history.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "cash": round(cash, 2),
                "shares": shares,
                "close_price": round(close_price, 4),
                "portfolio_value": round(total_value, 2),
            })

        # 回测结束时仍持股则按最后收盘价平仓
        if shares > 0:
            last_date = dates[-1]
            close_price = df.loc[last_date, "close"]
            price = close_price * (1 - self.slippage)
            revenue = shares * price * (1 - self.commission)
            profit = revenue - (last_buy_price or price) * shares * (1 + self.commission)
            trades.append({
                "date": last_date.strftime("%Y-%m-%d"),
                "action": "SELL",
                "shares": shares,
                "price": round(price, 4),
                "revenue": round(revenue, 2),
                "profit": round(profit, 2),
            })
            cash += revenue
            shares = 0

        # ── 绩效计算 ─────────────────────────────────────
        if not portfolio_history:
            return {"error": "无法计算绩效（无交易日数据）"}

        initial = self.initial_capital
        final = cash
        total_return = (final - initial) / initial

        days = (datetime.strptime(end_date, "%Y%m%d") - datetime.strptime(start_date, "%Y%m%d")).days
        annualized_return = (1 + total_return) ** (365 / max(days, 1)) - 1

        # 最大回撤
        pv_list = [p["portfolio_value"] for p in portfolio_history]
        max_drawdown = calculate_max_drawdown(pv_list)

        # 夏普比率
        if len(pv_list) > 1:
            daily_returns = [(pv_list[i] - pv_list[i - 1]) / pv_list[i - 1] for i in range(1, len(pv_list))]
            sharpe = calculate_sharpe_ratio(daily_returns)
        else:
            sharpe = 0.0

        # 胜率（配对买卖计算）
        sell_trades = [t for t in trades if t["action"] == "SELL"]
        win_trades = [t for t in sell_trades if t.get("profit", 0) > 0]
        win_rate = len(win_trades) / len(sell_trades) if sell_trades else 0.0

        return {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": self.initial_capital,
            "final_capital": round(final, 2),
            "total_return": round(total_return, 4),
            "annualized_return": round(annualized_return, 4),
            "max_drawdown": round(max_drawdown, 4),
            "sharpe_ratio": round(sharpe, 4),
            "win_rate": round(win_rate, 4),
            "total_trades": len(trades),
            "trades": trades,
            "portfolio_history": portfolio_history,
        }
