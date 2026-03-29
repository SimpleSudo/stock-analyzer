"""
事件驱动回测引擎
- 基于 EventTrigger 列表生成信号
- 支持多事件组合（需多数事件同方向才触发）
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

import pandas as pd
import numpy as np

from .engine import BacktestEngine
from .events import EventTrigger, EventSignal, create_triggers
from .metrics import calculate_sharpe_ratio, calculate_max_drawdown

logger = logging.getLogger(__name__)


class EventDrivenEngine(BacktestEngine):
    """事件驱动回测引擎"""

    def __init__(
        self,
        triggers: List[EventTrigger] = None,
        min_consensus: int = 1,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.triggers = triggers or []
        self.min_consensus = min_consensus  # 最少需要 N 个事件同方向才触发

    def _event_signal(self, df: pd.DataFrame, idx: int) -> str:
        """通过事件触发器生成综合信号"""
        buy_votes = 0
        sell_votes = 0
        events_fired = []

        for trigger in self.triggers:
            signal = trigger.check(df, idx)
            if signal is not None:
                events_fired.append(signal)
                if signal.action == "BUY":
                    buy_votes += signal.confidence
                elif signal.action == "SELL":
                    sell_votes += signal.confidence

        if buy_votes >= self.min_consensus and buy_votes > sell_votes:
            return "BUY"
        if sell_votes >= self.min_consensus and sell_votes > buy_votes:
            return "SELL"
        return "HOLD"

    def run_event_backtest(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        event_names: List[str] = None,
    ) -> Dict:
        """运行事件驱动回测"""
        df = self.fetch_historical_data(symbol, start_date, end_date)
        if df.empty:
            return {"error": "无法获取历史数据"}

        if event_names:
            self.triggers = create_triggers(event_names)

        if not self.triggers:
            return {"error": "未指定事件触发器"}

        cash = self.initial_capital
        shares = 0
        trades = []
        portfolio_history = []
        last_buy_price = None
        events_log = []

        dates = df.index
        for i in range(60, len(dates) - 1):  # 前 60 天预热
            current_date = dates[i]
            next_date = dates[i + 1]
            signal = self._event_signal(df, i)

            open_price = df.loc[next_date, "open"]

            if signal == "BUY" and shares == 0:
                price = open_price * (1 + self.slippage)
                max_shares = int(cash // (price * (1 + self.commission)))
                max_shares = (max_shares // 100) * 100
                if max_shares > 0:
                    cost = max_shares * price * (1 + self.commission)
                    shares = max_shares
                    cash -= cost
                    last_buy_price = price
                    trades.append({
                        "date": next_date.strftime("%Y-%m-%d"),
                        "action": "BUY", "shares": max_shares,
                        "price": round(price, 4), "cost": round(cost, 2),
                    })

            elif signal == "SELL" and shares > 0:
                price = open_price * (1 - self.slippage)
                revenue = shares * price * (1 - self.commission)
                profit = revenue - (last_buy_price or price) * shares * (1 + self.commission)
                trades.append({
                    "date": next_date.strftime("%Y-%m-%d"),
                    "action": "SELL", "shares": shares,
                    "price": round(price, 4), "revenue": round(revenue, 2),
                    "profit": round(profit, 2),
                })
                cash += revenue
                shares = 0
                last_buy_price = None

            close_price = df.loc[current_date, "close"]
            total_value = cash + shares * close_price
            portfolio_history.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "portfolio_value": round(total_value, 2),
            })

        # 结束时平仓
        if shares > 0:
            last_date = dates[-1]
            price = df.loc[last_date, "close"] * (1 - self.slippage)
            revenue = shares * price * (1 - self.commission)
            profit = revenue - (last_buy_price or price) * shares * (1 + self.commission)
            trades.append({
                "date": last_date.strftime("%Y-%m-%d"),
                "action": "SELL", "shares": shares,
                "price": round(price, 4), "revenue": round(revenue, 2),
                "profit": round(profit, 2),
            })
            cash += revenue

        # 绩效
        if not portfolio_history:
            return {"error": "无交易日数据"}

        final = cash
        total_return = (final - self.initial_capital) / self.initial_capital
        pv_list = [p["portfolio_value"] for p in portfolio_history]
        max_drawdown = calculate_max_drawdown(pv_list)

        sell_trades = [t for t in trades if t["action"] == "SELL"]
        win_trades = [t for t in sell_trades if t.get("profit", 0) > 0]

        return {
            "symbol": symbol,
            "engine": "EventDriven",
            "events": [t.name for t in self.triggers],
            "initial_capital": self.initial_capital,
            "final_capital": round(final, 2),
            "total_return": round(total_return, 4),
            "max_drawdown": round(max_drawdown, 4),
            "total_trades": len(trades),
            "win_rate": round(len(win_trades) / len(sell_trades), 4) if sell_trades else 0,
            "trades": trades,
            "portfolio_history": portfolio_history,
        }
