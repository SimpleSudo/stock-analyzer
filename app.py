import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
import plotly.graph_objects as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="A股分析系统", layout="wide")

st.title("📈 A股智能分析系统")
st.caption("输入股票代码或名称，获取多维度AI分析与买入建议")

# Sidebar
st.sidebar.header("设置")
stock_input = st.sidebar.text_input("股票代码或名称", "000001")
analyze_btn = st.sidebar.button("开始分析", type="primary")

# Helper functions
def get_stock_data(symbol):
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
        st.error(f"获取数据失败: {e}")
        return None

def calculate_indicators(df):
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

def generate_signal(df):
    """Generate buy/sell signal based on indicators"""
    if df is None or len(df) < 60:
        return "数据不足", 0
    
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

# Main
if analyze_btn:
    with st.spinner("正在获取数据并分析..."):
        df = get_stock_data(stock_input)
        if df is not None:
            df = calculate_indicators(df)
            signal, score, reasons = generate_signal(df)
            
            # Display results
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader(f"{stock_input} 最近走势")
                fig = plt.Figure()
                fig.add_trace(plt.Candlestick(x=df.index,
                                              open=df['open'],
                                              high=df['high'],
                                              low=df['low'],
                                              close=df['close'],
                                              name="K线"))
                fig.add_trace(plt.Scatter(x=df.index, y=df['MA5'], name="MA5", line=dict(color='blue', width=1)))
                fig.add_trace(plt.Scatter(x=df.index, y=df['MA20'], name="MA20", line=dict(color='orange', width=1)))
                fig.update_layout(title=f"{stock_input} K线图与均线", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                
                # Indicators
                st.subheader("技术指标")
                indicator_col1, indicator_col2, indicator_col3 = st.columns(3)
                with indicator_col1:
                    st.metric("MA5", f"{df['MA5'].iloc[-1]:.2f}")
                    st.metric("MA20", f"{df['MA20'].iloc[-1]:.2f}")
                    st.metric("MA60", f"{df['MA60'].iloc[-1]:.2f}")
                with indicator_col2:
                    st.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")
                    st.metric("MACD", f"{df['MACD'].iloc[-1]:.4f}")
                    st.metric("Signal", f"{df['Signal'].iloc[-1]:.4f}")
                with indicator_col3:
                    st.metric("布林上轨", f"{df['BB_upper'].iloc[-1]:.2f}")
                    st.metric("布林中轨", f"{df['BB_mid'].iloc[-1]:.2f}")
                    st.metric("布林下轨", f"{df['BB_lower'].iloc[-1]:.2f}")
            
            with col2:
                st.subheader("📊 分析结论")
                st.markdown(f"### 信号: **{signal}**")
                st.markdown(f"**评分**: {score} （-10 ~ +10）")
                st.markdown("**依据**:")
                for r in reasons:
                    st.markdown(f"- {r}")
                
                # Latest price
                latest_price = df['close'].iloc[-1]
                change_pct = df['change_pct'].iloc[-1]
                st.metric("最新价", f"{latest_price:.2f}", f"{change_pct:.2f}%")
                
                # Buy point suggestion
                if score > 0:
                    st.success("💡 建议买入区间: 近期低点或回调至MA10附近")
                else:
                    st.warning("💡 建议观望或等待更好时机")
            
            # Show recent data
            with st.expander("查看最近交易数据"):
                st.dataframe(df.tail(10)[['open', 'high', 'low', 'close', 'volume']])
        else:
            st.error("无法获取股票数据，请检查代码是否正确。")

# Stock list for recommendation (simple example)
st.sidebar.markdown("---")
st.sidebar.subheader("🔥 今日热门")
if st.sidebar.button("刷新推荐列表"):
    # For demo, we'll show some hardcoded popular stocks
    popular = ["000001", "000002", "600000", "600036", "000858"]
    st.sidebar.write("热门股票代码:")
    for code in popular:
        st.sidebar.write(f"- {code}")

# Footer
st.markdown("---")
st.caption("⚠️ 免责声明: 本系统仅供学习参考，不构成投资建议。股市有风险，投资需谨慎.")