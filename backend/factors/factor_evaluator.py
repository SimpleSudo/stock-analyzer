"""
因子评估器 - IC/ICIR 计算与动态权重
"""
import numpy as np
import pandas as pd
from typing import Dict, List
from .factor_library import FACTOR_REGISTRY


def calculate_ic(factor_values: pd.Series, forward_returns: pd.Series) -> float:
    """计算信息系数 (IC) — 因子值与未来收益的 Spearman 相关系数"""
    valid = pd.DataFrame({"factor": factor_values, "return": forward_returns}).dropna()
    if len(valid) < 20:
        return 0.0
    return float(valid["factor"].corr(valid["return"], method="spearman"))


def calculate_icir(ic_series: pd.Series) -> float:
    """ICIR = IC 均值 / IC 标准差 — 越高说明因子越稳定有效"""
    if len(ic_series) < 5 or ic_series.std() == 0:
        return 0.0
    return float(ic_series.mean() / ic_series.std())


def evaluate_factors(
    df: pd.DataFrame,
    forward_days: int = 5,
    rolling_window: int = 60,
) -> Dict[str, Dict]:
    """
    评估所有注册因子的有效性
    :return: {factor_name: {ic, icir, weight, category}}
    """
    if len(df) < rolling_window + forward_days + 10:
        # 数据不足，返回等权
        n = len(FACTOR_REGISTRY)
        return {
            name: {"ic": 0, "icir": 0, "weight": 1.0 / n, "category": info["category"]}
            for name, info in FACTOR_REGISTRY.items()
        }

    forward_returns = df["close"].pct_change(forward_days).shift(-forward_days)

    results = {}
    for name, info in FACTOR_REGISTRY.items():
        try:
            factor_vals = info["fn"](df)
            # 滚动 IC
            ic_list = []
            for i in range(rolling_window, len(df) - forward_days, 20):
                window_factor = factor_vals.iloc[i - rolling_window:i]
                window_return = forward_returns.iloc[i - rolling_window:i]
                ic = calculate_ic(window_factor, window_return)
                ic_list.append(ic)

            ic_series = pd.Series(ic_list)
            avg_ic = float(ic_series.mean()) if len(ic_series) > 0 else 0
            icir = calculate_icir(ic_series)

            results[name] = {
                "ic": round(avg_ic, 4),
                "icir": round(icir, 4),
                "weight": 0,  # 稍后计算
                "category": info["category"],
            }
        except Exception:
            results[name] = {"ic": 0, "icir": 0, "weight": 0, "category": info["category"]}

    # 动态权重：基于 abs(ICIR) 分配
    total_icir = sum(abs(r["icir"]) for r in results.values())
    if total_icir > 0:
        for name in results:
            results[name]["weight"] = round(abs(results[name]["icir"]) / total_icir, 4)
    else:
        # 等权
        n = len(results)
        for name in results:
            results[name]["weight"] = round(1.0 / n, 4)

    return results


def calculate_composite_score(df: pd.DataFrame, factor_weights: Dict[str, Dict] = None) -> float:
    """
    计算动态加权的综合因子评分（最新一行）
    :return: -10 ~ +10 的综合分
    """
    if factor_weights is None:
        factor_weights = evaluate_factors(df)

    total_score = 0.0
    for name, info in factor_weights.items():
        fn = FACTOR_REGISTRY.get(name, {}).get("fn")
        if fn is None:
            continue
        try:
            vals = fn(df)
            latest = float(vals.iloc[-1]) if len(vals) > 0 and pd.notna(vals.iloc[-1]) else 0
            # 标准化到 [-1, 1] 范围
            all_vals = vals.dropna()
            if len(all_vals) > 10:
                mean = float(all_vals.mean())
                std = float(all_vals.std())
                if std > 0:
                    z = (latest - mean) / std
                    normalized = max(-1, min(1, z / 3))  # 3-sigma clip
                else:
                    normalized = 0
            else:
                normalized = 0
            total_score += normalized * info["weight"]
        except Exception:
            pass

    # 映射到 -10 ~ +10
    return round(total_score * 10, 2)
