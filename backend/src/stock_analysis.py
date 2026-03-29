"""
股票技术分析核心模块
- 通过 DataProvider 获取真实行情（AKShare 主 + Tushare 备）
- 计算完整历史指标时间序列（每个数据点都有 MA/RSI/MACD/BB）
- 绝不返回 mock 数据，所有错误明确上抛
- get_full_analysis() 提供完整多维度分析（技术+基本面+行业+资金+价格目标+AI报告）
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

from data.provider_factory import get_history_with_fallback
from data.base_provider import DataProviderError
from utils.cache import stock_data_cache, fundamental_cache
from .price_targets import calculate_price_targets
from .industry_analysis import get_industry_comparison
from .capital_flow import get_capital_flow
from .llm_reporter import generate_analysis_report


def get_stock_data(symbol: str) -> Tuple[pd.DataFrame, str]:
    """
    获取历史行情数据（自动故障转移 + TTL 缓存）。

    :return: (df, provider_name)
    :raises DataProviderError: 所有数据源均失败时抛出
    """
    cache_key = f"hist:{symbol}"
    cached = stock_data_cache.get(cache_key)
    if cached is not None:
        return cached

    start_date = "20240101"
    end_date = datetime.now().strftime("%Y%m%d")
    result = get_history_with_fallback(symbol, start_date, end_date)
    stock_data_cache.set(cache_key, result, ttl=300)
    return result


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算全部技术指标，每个历史数据点都有对应值（非单一最新值）。
    返回的 DataFrame 包含原始 OHLCV 以及所有指标列。
    """
    df = df.copy()

    # 移动平均线（历史序列）
    df["ma5"]  = df["close"].rolling(window=5).mean()
    df["ma10"] = df["close"].rolling(window=10).mean()
    df["ma20"] = df["close"].rolling(window=20).mean()
    df["ma60"] = df["close"].rolling(window=60).mean()

    # RSI（历史序列）
    delta    = df["close"].diff()
    up       = delta.clip(lower=0)
    down     = -delta.clip(upper=0)
    roll_up  = up.rolling(window=14).mean()
    roll_dn  = down.rolling(window=14).mean()
    rs       = roll_up / roll_dn
    df["rsi"] = 100 - (100 / (1 + rs))

    # MACD（历史序列）
    exp12       = df["close"].ewm(span=12, adjust=False).mean()
    exp26       = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"]  = exp12 - exp26
    df["signal_line"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["hist"]  = df["macd"] - df["signal_line"]

    # 布林带（历史序列）
    df["bb_mid"]   = df["close"].rolling(window=20).mean()
    bb_std         = df["close"].rolling(window=20).std()
    df["bb_upper"] = df["bb_mid"] + 2 * bb_std
    df["bb_lower"] = df["bb_mid"] - 2 * bb_std

    # KDJ（随机指标，9/3/3）
    low_9  = df["low"].rolling(window=9).min()
    high_9 = df["high"].rolling(window=9).max()
    rsv = (df["close"] - low_9) / (high_9 - low_9) * 100
    rsv = rsv.fillna(50)
    df["kdj_k"] = rsv.ewm(com=2, adjust=False).mean()
    df["kdj_d"] = df["kdj_k"].ewm(com=2, adjust=False).mean()
    df["kdj_j"] = 3 * df["kdj_k"] - 2 * df["kdj_d"]

    # WR（威廉指标，14日）
    high_14 = df["high"].rolling(window=14).max()
    low_14  = df["low"].rolling(window=14).min()
    df["wr"] = (high_14 - df["close"]) / (high_14 - low_14) * (-100)

    # OBV（能量潮）
    obv = [0]
    for i in range(1, len(df)):
        if df["close"].iloc[i] > df["close"].iloc[i - 1]:
            obv.append(obv[-1] + df["volume"].iloc[i])
        elif df["close"].iloc[i] < df["close"].iloc[i - 1]:
            obv.append(obv[-1] - df["volume"].iloc[i])
        else:
            obv.append(obv[-1])
    df["obv"] = obv

    # ATR（真实波动幅度，14日）
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - df["close"].shift(1)).abs()
    tr3 = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["atr"] = tr.rolling(window=14).mean()

    return df


def generate_signal(df: pd.DataFrame) -> Tuple[str, int, List[str]]:
    """根据最新指标值生成买卖信号"""
    if df is None or len(df) < 60:
        return "数据不足", 0, ["历史数据不足60条，无法进行有效分析"]

    latest = df.iloc[-1]
    prev   = df.iloc[-2]

    score   = 0
    reasons = []

    # MA 均线交叉
    if pd.notna(latest["ma5"]) and pd.notna(latest["ma10"]):
        if latest["ma5"] > latest["ma10"] and prev["ma5"] <= prev["ma10"]:
            score += 2
            reasons.append("MA5 上穿 MA10（金叉）")
        elif latest["ma5"] < latest["ma10"] and prev["ma5"] >= prev["ma10"]:
            score -= 2
            reasons.append("MA5 下穿 MA10（死叉）")

    # RSI
    if pd.notna(latest["rsi"]):
        if latest["rsi"] < 30:
            score += 2
            reasons.append(f"RSI={latest['rsi']:.1f}，超卖区间，有反弹机会")
        elif latest["rsi"] > 70:
            score -= 2
            reasons.append(f"RSI={latest['rsi']:.1f}，超买区间，注意回调风险")
        elif 30 <= latest["rsi"] <= 50:
            score += 1
            reasons.append(f"RSI={latest['rsi']:.1f}，处于合理区间")

    # MACD
    if pd.notna(latest["macd"]) and pd.notna(latest["signal_line"]):
        if latest["macd"] > latest["signal_line"] and prev["macd"] <= prev["signal_line"]:
            score += 2
            reasons.append("MACD 金叉，动能转正")
        elif latest["macd"] < latest["signal_line"] and prev["macd"] >= prev["signal_line"]:
            score -= 2
            reasons.append("MACD 死叉，动能转负")

    # 布林带
    if pd.notna(latest["bb_lower"]) and pd.notna(latest["bb_upper"]):
        if latest["close"] < latest["bb_lower"]:
            score += 2
            reasons.append("价格触及布林带下轨，超卖信号")
        elif latest["close"] > latest["bb_upper"]:
            score -= 2
            reasons.append("价格触及布林带上轨，超买信号")

    # 长期趋势（MA60）
    if pd.notna(latest["ma60"]):
        if latest["close"] > latest["ma60"]:
            score += 1
            reasons.append(f"价格在 MA60({latest['ma60']:.2f}) 之上，长期趋势向上")
        else:
            score -= 1
            reasons.append(f"价格在 MA60({latest['ma60']:.2f}) 之下，长期趋势向下")

    # KDJ
    if pd.notna(latest.get("kdj_k")) and pd.notna(latest.get("kdj_d")):
        k, d, j = latest["kdj_k"], latest["kdj_d"], latest.get("kdj_j", 50)
        if k < 20 and d < 20:
            score += 1
            reasons.append(f"KDJ 超卖区（K={k:.1f}, D={d:.1f}）")
        elif k > 80 and d > 80:
            score -= 1
            reasons.append(f"KDJ 超买区（K={k:.1f}, D={d:.1f}）")
        if pd.notna(prev.get("kdj_k")) and pd.notna(prev.get("kdj_d")):
            if k > d and prev["kdj_k"] <= prev["kdj_d"] and k < 50:
                score += 1
                reasons.append("KDJ 低位金叉")
            elif k < d and prev["kdj_k"] >= prev["kdj_d"] and k > 50:
                score -= 1
                reasons.append("KDJ 高位死叉")

    # WR 威廉指标
    if pd.notna(latest.get("wr")):
        wr = latest["wr"]
        if wr < -80:
            score += 1
            reasons.append(f"WR={wr:.1f}，超卖区间")
        elif wr > -20:
            score -= 1
            reasons.append(f"WR={wr:.1f}，超买区间")

    # 成交量放大
    if "volume" in df.columns:
        vol_ma5 = df["volume"].rolling(5).mean().iloc[-1]
        if pd.notna(vol_ma5) and vol_ma5 > 0 and latest["volume"] > vol_ma5 * 1.5:
            score += 1
            reasons.append("成交量较 5 日均量放大 50% 以上")

    # 信号判定
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

    if not reasons:
        reasons.append("指标中性，建议观望")

    return signal, score, reasons


def _round_or_none(val, decimals: int = 2) -> Optional[float]:
    """安全四舍五入，NaN 转 None"""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    try:
        return round(float(val), decimals)
    except (TypeError, ValueError):
        return None


def get_analysis(symbol: str) -> Dict:
    """
    获取股票完整分析结果。
    返回格式包含：
    - data.chart_with_indicators: 每个历史数据点都带完整指标时间序列
    - data.data_source: 使用的数据源名称
    """
    # 获取行情数据（会抛出 DataProviderError，不 catch 让上层处理）
    df, data_source = get_stock_data(symbol)

    # 计算指标（返回含历史序列的 DataFrame）
    df = calculate_indicators(df)

    # 生成信号
    signal, score, reasons = generate_signal(df)

    # 最新数据
    latest    = df.iloc[-1]
    prev_close = df["close"].iloc[-2] if len(df) > 1 else latest["close"]
    change     = latest["close"] - prev_close
    change_pct = (change / prev_close * 100) if prev_close != 0 else 0

    # 准备图表数据（最近 60 条，含完整指标序列）
    chart_df = df.tail(60).reset_index()
    chart_df["date"] = chart_df["date"].dt.strftime("%Y-%m-%d")

    chart_with_indicators = []
    for _, row in chart_df.iterrows():
        chart_with_indicators.append({
            "date":      row["date"],
            "open":      _round_or_none(row.get("open")),
            "high":      _round_or_none(row.get("high")),
            "low":       _round_or_none(row.get("low")),
            "close":     _round_or_none(row.get("close")),
            "volume":    int(row["volume"]) if pd.notna(row.get("volume")) else None,
            # 均线
            "ma5":       _round_or_none(row.get("ma5")),
            "ma10":      _round_or_none(row.get("ma10")),
            "ma20":      _round_or_none(row.get("ma20")),
            "ma60":      _round_or_none(row.get("ma60")),
            # RSI
            "rsi":       _round_or_none(row.get("rsi")),
            # MACD
            "macd":      _round_or_none(row.get("macd"), 4),
            "signal":    _round_or_none(row.get("signal_line"), 4),
            "hist":      _round_or_none(row.get("hist"), 4),
            # 布林带
            "bb_upper":  _round_or_none(row.get("bb_upper")),
            "bb_mid":    _round_or_none(row.get("bb_mid")),
            "bb_lower":  _round_or_none(row.get("bb_lower")),
            # KDJ
            "kdj_k":     _round_or_none(row.get("kdj_k")),
            "kdj_d":     _round_or_none(row.get("kdj_d")),
            "kdj_j":     _round_or_none(row.get("kdj_j")),
            # WR
            "wr":        _round_or_none(row.get("wr")),
            # OBV
            "obv":       int(row["obv"]) if pd.notna(row.get("obv")) else None,
            # ATR
            "atr":       _round_or_none(row.get("atr")),
        })

    # 兼容旧格式 chart 字段（只含 OHLCV）
    chart_simple = [
        {k: v for k, v in item.items() if k in ("date", "open", "high", "low", "close", "volume")}
        for item in chart_with_indicators
    ]

    # amount 字段（可能不存在）
    amount_val = _round_or_none(latest.get("amount", None)) or 0

    return {
        "symbol": symbol,
        "data": {
            "latest": {
                "price":      _round_or_none(latest["close"]),
                "change":     _round_or_none(change),
                "change_pct": _round_or_none(change_pct),
                "volume":     int(latest["volume"]) if pd.notna(latest["volume"]) else 0,
                "amount":     amount_val,
            },
            "chart":                  chart_simple,
            "chart_with_indicators":  chart_with_indicators,
            "data_source":            data_source,
        },
        "indicators": {
            "MA5":      _round_or_none(latest.get("ma5")),
            "MA10":     _round_or_none(latest.get("ma10")),
            "MA20":     _round_or_none(latest.get("ma20")),
            "MA60":     _round_or_none(latest.get("ma60")),
            "RSI":      _round_or_none(latest.get("rsi")),
            "MACD":     _round_or_none(latest.get("macd"), 4),
            "Signal":   _round_or_none(latest.get("signal_line"), 4),
            "BB_upper": _round_or_none(latest.get("bb_upper")),
            "BB_mid":   _round_or_none(latest.get("bb_mid")),
            "BB_lower": _round_or_none(latest.get("bb_lower")),
        },
        "signal":  signal,
        "score":   score,
        "reasons": reasons,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 基本面数据获取（供 get_full_analysis 使用）
# ──────────────────────────────────────────────────────────────────────────────

def _get_fundamental_data(symbol: str) -> dict:
    """
    获取股票基本面数据：PE(TTM)、PB、ROE、资产负债率、毛利率、股票名称。
    全部失败时返回空字典（不影响主流程）。结果缓存 1 小时。
    """
    cache_key = f"fund:{symbol}"
    cached = fundamental_cache.get(cache_key)
    if cached is not None:
        return cached

    result: dict = {}

    # ── 股票名称 ────────────────────────────────────────
    try:
        info_df = ak.stock_individual_info_em(symbol=symbol)
        if info_df is not None and not info_df.empty:
            info_dict = dict(zip(info_df.iloc[:, 0], info_df.iloc[:, 1]))
            result["name"] = info_dict.get("股票简称", symbol)
    except Exception:
        pass

    # ── PE(TTM) ──────────────────────────────────────────
    try:
        pe_df = ak.stock_zh_valuation_baidu(symbol=symbol, indicator="市盈率(TTM)")
        if pe_df is not None and not pe_df.empty:
            result["pe"] = float(pe_df.iloc[-1]["value"])
    except Exception:
        pass

    # ── PB ───────────────────────────────────────────────
    try:
        pb_df = ak.stock_zh_valuation_baidu(symbol=symbol, indicator="市净率")
        if pb_df is not None and not pb_df.empty:
            result["pb"] = float(pb_df.iloc[-1]["value"])
    except Exception:
        pass

    # ── ROE / 资产负债率 / 毛利率 ─────────────────────────
    try:
        fin_df = ak.stock_financial_abstract(symbol=symbol)
        if fin_df is not None and not fin_df.empty:
            latest = fin_df.iloc[0]
            # ROE
            for col in ["净资产收益率(%)", "净资产收益率", "ROE(%)"]:
                if col in fin_df.columns and pd.notna(latest.get(col)):
                    try:
                        result["roe"] = float(latest[col])
                        break
                    except (TypeError, ValueError):
                        pass
            # 资产负债率
            for col in ["资产负债率(%)", "资产负债率"]:
                if col in fin_df.columns and pd.notna(latest.get(col)):
                    try:
                        result["debt_ratio"] = float(latest[col])
                        break
                    except (TypeError, ValueError):
                        pass
            # 毛利率
            for col in ["销售毛利率(%)", "毛利率(%)", "销售毛利率"]:
                if col in fin_df.columns and pd.notna(latest.get(col)):
                    try:
                        result["gross_margin"] = float(latest[col])
                        break
                    except (TypeError, ValueError):
                        pass
    except Exception:
        pass

    fundamental_cache.set(cache_key, result, ttl=3600)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 完整多维度分析主函数
# ──────────────────────────────────────────────────────────────────────────────

def get_full_analysis(symbol: str, stock_name: Optional[str] = None) -> Dict:
    """
    获取股票完整多维度分析结果。
    包含：技术分析、基本面、行业对比、资金流向、价格目标、AI分析报告。

    :param symbol:     6 位股票代码（已 resolve）
    :param stock_name: 可选，股票名称（从 symbol_resolver 传入，避免重复请求）
    :return: 完整分析结果字典
    """
    # ── 第一步：获取历史行情 + 计算技术指标 ──────────────
    df_raw, data_source = get_stock_data(symbol)
    df = calculate_indicators(df_raw)
    signal, score, reasons = generate_signal(df)

    latest     = df.iloc[-1]
    prev_close = df["close"].iloc[-2] if len(df) > 1 else latest["close"]
    change     = latest["close"] - prev_close
    change_pct = (change / prev_close * 100) if prev_close != 0 else 0.0
    current_price = float(_round_or_none(latest["close"]) or 0)

    # 图表数据
    chart_df = df.tail(60).reset_index()
    chart_df["date"] = chart_df["date"].dt.strftime("%Y-%m-%d")
    chart_with_indicators = []
    for _, row in chart_df.iterrows():
        chart_with_indicators.append({
            "date":     row["date"],
            "open":     _round_or_none(row.get("open")),
            "high":     _round_or_none(row.get("high")),
            "low":      _round_or_none(row.get("low")),
            "close":    _round_or_none(row.get("close")),
            "volume":   int(row["volume"]) if pd.notna(row.get("volume")) else None,
            "ma5":      _round_or_none(row.get("ma5")),
            "ma10":     _round_or_none(row.get("ma10")),
            "ma20":     _round_or_none(row.get("ma20")),
            "ma60":     _round_or_none(row.get("ma60")),
            "rsi":      _round_or_none(row.get("rsi")),
            "macd":     _round_or_none(row.get("macd"), 4),
            "signal":   _round_or_none(row.get("signal_line"), 4),
            "hist":     _round_or_none(row.get("hist"), 4),
            "bb_upper": _round_or_none(row.get("bb_upper")),
            "bb_mid":   _round_or_none(row.get("bb_mid")),
            "bb_lower": _round_or_none(row.get("bb_lower")),
        })
    chart_simple = [
        {k: v for k, v in item.items() if k in ("date", "open", "high", "low", "close", "volume")}
        for item in chart_with_indicators
    ]
    amount_val = _round_or_none(latest.get("amount", None)) or 0

    base_result = {
        "symbol": symbol,
        "data": {
            "latest": {
                "price":      current_price,
                "change":     _round_or_none(change),
                "change_pct": _round_or_none(change_pct),
                "volume":     int(latest["volume"]) if pd.notna(latest["volume"]) else 0,
                "amount":     amount_val,
            },
            "chart":                 chart_simple,
            "chart_with_indicators": chart_with_indicators,
            "data_source":           data_source,
        },
        "indicators": {
            "MA5":      _round_or_none(latest.get("ma5")),
            "MA10":     _round_or_none(latest.get("ma10")),
            "MA20":     _round_or_none(latest.get("ma20")),
            "MA60":     _round_or_none(latest.get("ma60")),
            "RSI":      _round_or_none(latest.get("rsi")),
            "MACD":     _round_or_none(latest.get("macd"), 4),
            "Signal":   _round_or_none(latest.get("signal_line"), 4),
            "BB_upper": _round_or_none(latest.get("bb_upper")),
            "BB_mid":   _round_or_none(latest.get("bb_mid")),
            "BB_lower": _round_or_none(latest.get("bb_lower")),
        },
        "signal":  signal,
        "score":   score,
        "reasons": reasons,
    }

    # ── 第二步：并发获取基本面、资金流向、价格目标 ────────
    fund_result: dict = {}
    price_targets_result = None
    capital_flow_result = None

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures: dict = {
            executor.submit(_get_fundamental_data, symbol): "fundamental",
            executor.submit(get_capital_flow, symbol):     "capital_flow",
            executor.submit(calculate_price_targets, df, current_price): "price_targets",
        }
        for future in as_completed(futures, timeout=25):
            key = futures[future]
            try:
                val = future.result()
                if key == "fundamental":
                    fund_result = val or {}
                elif key == "capital_flow":
                    capital_flow_result = val
                elif key == "price_targets":
                    price_targets_result = val
            except Exception:
                pass  # 某项失败不影响其他

    # ── 第三步：行业对比（依赖基本面 PE/PB/ROE）────────────
    industry_result = None
    try:
        industry_result = get_industry_comparison(
            symbol,
            stock_pe=fund_result.get("pe"),
            stock_pb=fund_result.get("pb"),
            stock_roe=fund_result.get("roe"),
        )
    except Exception:
        pass

    # ── 第四步：整合基本面字典（供 LLM 和前端使用）─────────
    name = stock_name or fund_result.get("name", symbol)
    fundamental_dict = {
        "pe":           fund_result.get("pe"),
        "pb":           fund_result.get("pb"),
        "roe":          fund_result.get("roe"),
        "debt_ratio":   fund_result.get("debt_ratio"),
        "gross_margin": fund_result.get("gross_margin"),
    }
    tech_dict = {
        "rsi":     base_result["indicators"].get("RSI"),
        "macd":    base_result["indicators"].get("MACD"),
        "ma20":    base_result["indicators"].get("MA20"),
        "ma60":    base_result["indicators"].get("MA60"),
        "score":   score,
        "signal":  signal,
        "reasons": reasons,
    }

    # ── 第五步：LLM AI 分析报告 ──────────────────────────
    ai_report = None
    try:
        ai_report = generate_analysis_report(
            symbol=symbol,
            name=name,
            current_price=current_price,
            change_pct=float(change_pct),
            tech=tech_dict,
            fundamental=fundamental_dict,
            industry=industry_result,
            capital_flow=capital_flow_result,
            price_targets=price_targets_result,
        )
    except Exception:
        pass

    return {
        **base_result,
        "name":          name,
        "fundamental":   fundamental_dict,
        "price_targets": price_targets_result,
        "industry":      industry_result,
        "capital_flow":  capital_flow_result,
        "ai_report":     ai_report,
    }
