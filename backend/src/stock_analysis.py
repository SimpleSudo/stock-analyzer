import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

def get_stock_data(symbol: str) -> Optional[pd.DataFrame]:
    """Fetch historical data for A-share"""
    try:
        # akshare needs symbol without exchange prefix for A-shares
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date="2024-01-01", end_date=datetime.now().strftime('%Y%m%d'), adjust="")
        if df.empty:
            return None
        df = df.rename(columns={
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "涨跌幅": "change_pct",
            "涨跌额": "change",
            "换手率": "turnover"
        })
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate technical indicators"""
    # Moving averages
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA10'] = df['close'].rolling(window=10).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA60'] = df['close'].rolling(window=60).mean()
    
    # RSI
    delta = df['close'].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.rolling(window=14).mean()
    roll_down = down.rolling(window=14).mean()
    RS = roll_up / roll_down
    df['RSI'] = 100 - (100 / (1 + RS))
    
    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Hist'] = df['MACD'] - df['Signal']
    
    # Bollinger Bands
    df['BB_mid'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_mid'] + 2 * bb_std
    df['BB_lower'] = df['BB_mid'] - 2 * bb_std
    
    return df

def generate_signal(df: pd.DataFrame) -> Tuple[str, int, List[str]]:
    """Generate buy/sell signal based on indicators"""
    if df is None or len(df) < 60:
        return "数据不足", 0, ["数据不足"]
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    score = 0
    reasons = []
    
    # MA crossover
    if latest['MA5'] > latest['MA10'] and prev['MA5'] <= prev['MA10']:
        score += 2
        reasons.append("MA5 上穿 MA10")
    elif latest['MA5'] < latest['MA10'] and prev['MA5'] >= prev['MA10']:
        score -= 2
        reasons.append("MA5 下穿 MA10")
    
    # RSI
    if latest['RSI'] < 30:
        score += 2
        reasons.append("RSI 超卖 (<30)")
    elif latest['RSI'] > 70:
        score -= 2
        reasons.append("RSI 超买 (>70)")
    elif 30 <= latest['RSI'] <= 50:
        score += 1
        reasons.append("RSI 在合理区间")
    
    # MACD
    if latest['MACD'] > latest['Signal'] and prev['MACD'] <= prev['Signal']:
        score += 2
        reasons.append("MACD 金叉")
    elif latest['MACD'] < latest['Signal'] and prev['MACD'] >= prev['Signal']:
        score -= 2
        reasons.append("MACD 死叉")
    
    # Price vs Bollinger
    if latest['close'] < latest['BB_lower']:
        score += 2
        reasons.append("价格触及布林带下轨")
    elif latest['close'] > latest['BB_upper']:
        score -= 2
        reasons.append("价格触及布林带上轨")
    
    # Trend
    if latest['close'] > latest['MA60']:
        score += 1
        reasons.append("价格在MA60之上 (长期趋势向上)")
    else:
        score -= 1
        reasons.append("价格在MA60之下 (长期趋势向下)")
    
    # Volume
    vol_ma5 = df['volume'].rolling(5).mean().iloc[-1]
    if latest['volume'] > vol_ma5 * 1.5:
        score += 1
        reasons.append("成交量放大")
    
    # Determine signal
    if score >= 3:
        signal = "强烈买入"
    elif score >= 1:
        signal = "买入"
    elif score <= -3:
        signal = "强烈卖出"
    elif score <= -1:
        signal = "卖出"
    else:
        signal = "观望"
    
    return signal, score, reasons

def get_analysis(symbol: str) -> Dict:
    """Get complete analysis for a stock symbol"""
    df = get_stock_data(symbol)
    if df is None:
        return {
            "symbol": symbol,
            "error": "无法获取股票数据",
            "data": None,
            "indicators": {},
            "signal": "错误",
            "score": 0,
            "reasons": ["数据获取失败"]
        }
    
    df = calculate_indicators(df)
    signal, score, reasons = generate_signal(df)
    
    # Prepare latest data for frontend
    latest = df.iloc[-1]
    prev_close = df['close'].iloc[-2] if len(df) > 1 else latest['close']
    change = latest['close'] - prev_close
    change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
    
    # Prepare chart data (last 30 days)
    chart_data = df.tail(30).reset_index()
    chart_data['date'] = chart_data['date'].dt.strftime('%Y-%m-%d')
    
    return {
        "symbol": symbol,
        "data": {
            "latest": {
                "price": round(latest['close'], 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "volume": int(latest['volume']),
                "amount": round(latest['amount'], 2)
            },
            "chart": chart_data[['date', 'open', 'high', 'low', 'close', 'volume']].to_dict('records')
        },
        "indicators": {
            "MA5": round(latest['MA5'], 2) if not pd.isna(latest['MA5']) else None,
            "MA10": round(latest['MA10'], 2) if not pd.isna(latest['MA10']) else None,
            "MA20": round(latest['MA20'], 2) if not pd.isna(latest['MA20']) else None,
            "MA60": round(latest['MA60'], 2) if not pd.isna(latest['MA60']) else None,
            "RSI": round(latest['RSI'], 2) if not pd.isna(latest['RSI']) else None,
            "MACD": round(latest['MACD'], 4) if not pd.isna(latest['MACD']) else None,
            "Signal": round(latest['Signal'], 4) if not pd.isna(latest['Signal']) else None,
            "BB_upper": round(latest['BB_upper'], 2) if not pd.isna(latest['BB_upper']) else None,
            "BB_mid": round(latest['BB_mid'], 2) if not pd.isna(latest['BB_mid']) else None,
            "BB_lower": round(latest['BB_lower'], 2) if not pd.isna(latest['BB_lower']) else None
        },
        "signal": signal,
        "score": score,
        "reasons": reasons
    }
