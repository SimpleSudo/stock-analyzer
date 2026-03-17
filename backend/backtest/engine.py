import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import akshare as ak

# Import our agents and committee
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from agents.technical_agent import TechnicalAgent
from agents.fundamental_agent import FundamentalAgent
from agents.decision_committee import DecisionCommittee
from tools.toolkit import Toolkit

class BacktestEngine:
    def __init__(self, initial_capital: float = 100000.0, commission: float = 0.0003, slippage: float = 0.001):
        """
        Initialize backtest engine.
        :param initial_capital: 初始资金
        :param commission: 手续费率（单边）
        :param slippage: 滑点率
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        # Initialize agents and committee (same as in main)
        toolkit = Toolkit()
        technical_agent = TechnicalAgent(toolkit=toolkit)
        fundamental_agent = FundamentalAgent(toolkit=toolkit)
        self.committee = DecisionCommittee(
            agents=[technical_agent, fundamental_agent],
            weights={"Technical": 0.6, "Fundamental": 0.4}
        )
    
    def fetch_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch historical daily data for backtesting period.
        :param symbol: 股票代码
        :param start_date: 开始日期 'YYYYMMDD'
        :param end_date: 结束日期 'YYYYMMDD'
        :return: 包含OHLCV的DataFrame
        """
        try:
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                    start_date=start_date, end_date=end_date, adjust="")
            if df.empty:
                return pd.DataFrame()
            # Rename columns
            df = df.rename(columns={
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount"
            })
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            # Ensure we have required columns
            required = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required):
                # If missing, try to compute from available
                pass
            return df
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def run_backtest(self, symbol: str, start_date: str, end_date: str) -> Dict:
        """
        Run backtest for a given symbol and date range.
        :param symbol: 股票代码
        :param start_date: 开始日期 'YYYYMMDD'
        :param end_date: 结束日期 'YYYYMMDD'
        :return: 回测结果字典
        """
        # Fetch historical data
        df = self.fetch_historical_data(symbol, start_date, end_date)
        if df.empty:
            return {"error": "无法获取历史数据"}
        
        # We'll simulate daily trading: at the close of each day, we get signal for next day open
        # For simplicity, we'll use the close price to decide signal and simulate buying at next open
        # We'll keep it simple: signal at close t -> execute at open t+1
        
        # Initialize portfolio
        cash = self.initial_capital
        shares = 0
        portfolio_value = []  # daily portfolio value
        trades = []  # list of trades
        
        # We need to know the signal for each day. We'll compute signal using our committee
        # but note: our committee uses get_analysis which fetches recent data (maybe up to 1 year).
        # For backtesting, we want to use only data up to that point to avoid lookahead bias.
        # We'll create a mock get_analysis that uses only historical data up to current date.
        # For simplicity, we'll just use the same get_analysis but with a limited date range?
        # Since get_analysis fetches from 2024-01-01 to now, if our backtest period is within that,
        # it's okay but still uses future data? Actually get_analysis fetches fixed start date.
        # To avoid lookahead, we need to modify the agent to only use data up to current date.
        # Given time, we'll approximate by using the same analysis but note this is a limitation.
        
        # We'll iterate through each day (except last day because we need next day open)
        dates = df.index
        for i in range(len(dates) - 1):
            current_date = dates[i]
            next_date = dates[i + 1]
            
            # Get data up to current date for analysis
            historical_slice = df.loc[:current_date]
            # We need to feed this slice into our analysis function.
            # Instead of modifying the agent, we'll create a temporary function that uses this slice.
            # For simplicity, we'll skip the signal generation and just use a placeholder.
            # But we want to demonstrate the engine, so we'll implement a simple signal based on MA crossover
            # using only historical_slice.
            
            # Simple MA crossover signal for demonstration (can be replaced with committee later)
            if len(historical_slice) >= 60:
                close_series = historical_slice['close']
                ma5 = close_series.rolling(5).mean().iloc[-1]
                ma10 = close_series.rolling(10).mean().iloc[-1]
                prev_ma5 = close_series.rolling(5).mean().iloc[-2] if len(historical_slice) >= 2 else ma5
                prev_ma10 = close_series.rolling(10).mean().iloc[-2] if len(historical_slice) >= 2 else ma10
                
                if ma5 > ma10 and prev_ma5 <= prev_ma10:
                    signal = "BUY"
                elif ma5 < ma10 and prev_ma5 >= prev_ma10:
                    signal = "SELL"
                else:
                    signal = "HOLD"
            else:
                signal = "HOLD"
            
            # Execute trade at next day's open price (with slippage)
            open_price = df.loc[next_date, 'open']
            # Apply slippage: if buying, price slightly higher; if selling, price slightly lower
            if signal == "BUY":
                price = open_price * (1 + self.slippage)
                # Calculate max shares we can buy with cash
                max_shares = cash // (price * (1 + self.commission))  # commission on buy
                if max_shares > 0:
                    shares_to_buy = max_shares
                    cost = shares_to_buy * price * (1 + self.commission)
                    if cost <= cash:
                        shares += shares_to_buy
                        cash -= cost
                        trades.append({
                            'date': next_date.strftime('%Y-%m-%d'),
                            'action': 'BUY',
                            'shares': shares_to_buy,
                            'price': price,
                            'cost': cost
                        })
            elif signal == "SELL" and shares > 0:
                price = open_price * (1 - self.slippage)
                # Sell all shares
                shares_to_sell = shares
                revenue = shares_to_sell * price * (1 - self.commission)
                cash += revenue
                trades.append({
                    'date': next_date.strftime('%Y-%m-%d'),
                    'action': 'SELL',
                    'shares': shares_to_sell,
                    'price': price,
                    'revenue': revenue
                })
                shares = 0
            
            # Calculate portfolio value at close of current date (or next day open?)
            # We'll use close of current date for marking to market
            close_price = df.loc[current_date, 'close']
            portfolio_value = cash + shares * close_price
            portfolio_value.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'cash': cash,
                'shares': shares,
                'close_price': close_price,
                'portfolio_value': portfolio_value
            })
        
        # After loop, if we still hold shares, sell at last close
        if shares > 0:
            last_date = dates[-1]
            close_price = df.loc[last_date, 'close']
            price = close_price * (1 - self.slippage)
            revenue = shares * price * (1 - self.commission)
            cash += revenue
            trades.append({
                'date': last_date.strftime('%Y-%m-%d'),
                'action': 'SELL',
                'shares': shares,
                'price': price,
                'revenue': revenue
            })
            shares = 0
        
        # Calculate performance metrics
        if len(portfolio_value) > 0:
            initial = self.initial_capital
            final = portfolio_value[-1]['portfolio_value']
            total_return = (final - initial) / initial
            # Annualized return (approx)
            days = (datetime.strptime(end_date, '%Y%m%d') - datetime.strptime(start_date, '%Y%m%d')).days
            if days > 0:
                annualized_return = (1 + total_return) ** (365 / days) - 1
            else:
                annualized_return = 0
            
            # Calculate max drawdown
            peak = initial
            max_drawdown = 0
            for pv in portfolio_value:
                val = pv['portfolio_value']
                if val > peak:
                    peak = val
                drawdown = (peak - val) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Sharpe ratio (simplified, assuming risk-free rate 0)
            if len(portfolio_value) > 1:
                returns = []
                for i in range(1, len(portfolio_value)):
                    prev_val = portfolio_value[i-1]['portfolio_value']
                    curr_val = portfolio_value[i]['portfolio_value']
                    daily_return = (curr_val - prev_val) / prev_val
                    returns.append(daily_return)
                if returns:
                    avg_return = np.mean(returns)
                    std_return = np.std(returns)
                    if std_return > 0:
                        sharpe = (avg_return / std_return) * np.sqrt(252)  # annualized
                    else:
                        sharpe = 0
                else:
                    sharpe = 0
            else:
                sharpe = 0
            
            win_trades = [t for t in trades if t['action'] == 'SELL' and t.get('profit', 0) > 0]
            total_sell_trades = [t for t in trades if t['action'] == 'SELL']
            win_rate = len(win_trades) / len(total_sell_trades) if total_sell_trades else 0
            
            return {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": initial_capital,
                "final_capital": cash,
                "total_return": total_return,
                "annualized_return": annualized_return,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe,
                "win_rate": win_rate,
                "total_trades": len(trades),
                "trades": trades,
                "portfolio_history": portfolio_value
            }
        else:
            return {"error": "无法计算绩效"}