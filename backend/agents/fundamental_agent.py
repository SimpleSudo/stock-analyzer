"""
基本面分析 Agent
- 使用 AKShare 获取 PE/PB/ROE/资产负债率/毛利率等指标
- 独立评分逻辑（不再复用技术分析结果）
"""
import logging
from .base_agent import BaseAgent
from utils.cache import fundamental_cache

logger = logging.getLogger(__name__)

# 评分标准阈值
_PE_THRESHOLDS = {"cheap": 15, "fair": 30, "expensive": 60}
_PB_THRESHOLDS = {"cheap": 1.5, "fair": 3.0, "expensive": 6.0}
_ROE_THRESHOLDS = {"excellent": 20, "good": 12, "poor": 5}
_DEBT_THRESHOLDS = {"low": 40, "medium": 60, "high": 80}


class FundamentalAgent(BaseAgent):
    def __init__(self, llm=None, toolkit=None):
        super().__init__("Fundamental", llm, toolkit)

    def analyze(self, symbol: str) -> dict:
        """
        对指定股票进行基本面分析。
        独立获取 PE/PB/ROE/负债率/毛利率，基于自身逻辑打分。
        """
        score = 0
        reasons = []
        indicators = {}

        try:
            fundamental = self._fetch_fundamental(symbol)
        except Exception as e:
            logger.warning("基本面数据获取失败 [%s]: %s", symbol, e)
            return {
                "agent": self.name,
                "score": 0,
                "signal": "观望",
                "reasons": [f"基本面数据获取失败: {e}"],
                "indicators": {},
                "data": None,
            }

        pe = fundamental.get("pe")
        pb = fundamental.get("pb")
        roe = fundamental.get("roe")
        debt_ratio = fundamental.get("debt_ratio")
        gross_margin = fundamental.get("gross_margin")

        # ── PE 评分 ───────────────────────────────────────
        if pe is not None and pe > 0:
            indicators["PE(TTM)"] = round(pe, 1)
            if pe < _PE_THRESHOLDS["cheap"]:
                score += 2
                reasons.append(f"PE={pe:.1f}，估值偏低（低于{_PE_THRESHOLDS['cheap']}）")
            elif pe < _PE_THRESHOLDS["fair"]:
                score += 1
                reasons.append(f"PE={pe:.1f}，估值合理")
            elif pe < _PE_THRESHOLDS["expensive"]:
                score -= 1
                reasons.append(f"PE={pe:.1f}，估值偏高")
            else:
                score -= 2
                reasons.append(f"PE={pe:.1f}，估值过高（超过{_PE_THRESHOLDS['expensive']}）")

        # ── PB 评分 ───────────────────────────────────────
        if pb is not None and pb > 0:
            indicators["PB"] = round(pb, 2)
            if pb < _PB_THRESHOLDS["cheap"]:
                score += 2
                reasons.append(f"PB={pb:.2f}，资产折价明显")
            elif pb < _PB_THRESHOLDS["fair"]:
                score += 1
                reasons.append(f"PB={pb:.2f}，估值合理")
            elif pb < _PB_THRESHOLDS["expensive"]:
                score -= 1
                reasons.append(f"PB={pb:.2f}，偏高")
            else:
                score -= 2
                reasons.append(f"PB={pb:.2f}，严重高估")

        # ── ROE 评分 ──────────────────────────────────────
        if roe is not None:
            indicators["ROE(%)"] = round(roe, 1)
            if roe >= _ROE_THRESHOLDS["excellent"]:
                score += 2
                reasons.append(f"ROE={roe:.1f}%，盈利能力优秀")
            elif roe >= _ROE_THRESHOLDS["good"]:
                score += 1
                reasons.append(f"ROE={roe:.1f}%，盈利能力良好")
            elif roe >= _ROE_THRESHOLDS["poor"]:
                reasons.append(f"ROE={roe:.1f}%，盈利能力一般")
            else:
                score -= 1
                reasons.append(f"ROE={roe:.1f}%，盈利能力较差")

        # ── 资产负债率评分 ────────────────────────────────
        if debt_ratio is not None:
            indicators["资产负债率(%)"] = round(debt_ratio, 1)
            if debt_ratio < _DEBT_THRESHOLDS["low"]:
                score += 1
                reasons.append(f"资产负债率={debt_ratio:.1f}%，财务安全")
            elif debt_ratio < _DEBT_THRESHOLDS["medium"]:
                reasons.append(f"资产负债率={debt_ratio:.1f}%，杠杆适中")
            elif debt_ratio < _DEBT_THRESHOLDS["high"]:
                score -= 1
                reasons.append(f"资产负债率={debt_ratio:.1f}%，杠杆较高")
            else:
                score -= 2
                reasons.append(f"资产负债率={debt_ratio:.1f}%，债务风险高")

        # ── 毛利率评分 ────────────────────────────────────
        if gross_margin is not None:
            indicators["毛利率(%)"] = round(gross_margin, 1)
            if gross_margin >= 50:
                score += 1
                reasons.append(f"毛利率={gross_margin:.1f}%，具有较强定价权")
            elif gross_margin >= 30:
                reasons.append(f"毛利率={gross_margin:.1f}%，盈利空间正常")
            elif gross_margin >= 15:
                score -= 1
                reasons.append(f"毛利率={gross_margin:.1f}%，盈利空间偏薄")
            else:
                score -= 1
                reasons.append(f"毛利率={gross_margin:.1f}%，盈利能力弱")

        if not reasons:
            reasons.append("基本面数据不足，无法给出评价")

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

        analysis_output = {
            "agent": self.name,
            "score": score,
            "signal": signal,
            "reasons": reasons,
            "indicators": indicators,
            "data": None,
        }

        try:
            self.store_analysis(symbol, analysis_output)
        except Exception as e:
            logger.warning("Failed to store fundamental analysis: %s", e)

        return analysis_output

    def _fetch_fundamental(self, symbol: str) -> dict:
        """获取基本面数据（缓存 1 小时），优先使用 Toolkit，失败回退到 AKShare 直接调用"""
        cache_key = f"agent_fund:{symbol}"
        cached = fundamental_cache.get(cache_key)
        if cached is not None:
            return cached

        import akshare as ak
        import pandas as pd

        result: dict = {}

        # PE / PB — 从实时行情获取
        try:
            spot_df = ak.stock_zh_a_spot_em()
            if spot_df is not None and not spot_df.empty:
                row = spot_df[spot_df["代码"] == symbol]
                if not row.empty:
                    r = row.iloc[0]
                    try:
                        result["pe"] = float(r.get("市盈率-动态"))
                    except (TypeError, ValueError):
                        pass
                    try:
                        result["pb"] = float(r.get("市净率"))
                    except (TypeError, ValueError):
                        pass
        except Exception:
            pass

        # ROE / 毛利率
        try:
            fin_df = ak.stock_financial_analysis_indicator(symbol=symbol, start_year="2023")
            if fin_df is not None and not fin_df.empty:
                latest = fin_df.iloc[0]
                for col in ["净资产收益率(%)", "ROE(%)", "加权净资产收益率(%)"]:
                    if col in fin_df.columns and pd.notna(latest.get(col)):
                        try:
                            result["roe"] = float(latest[col])
                            break
                        except (TypeError, ValueError):
                            pass
                for col in ["销售毛利率(%)", "毛利率(%)"]:
                    if col in fin_df.columns and pd.notna(latest.get(col)):
                        try:
                            result["gross_margin"] = float(latest[col])
                            break
                        except (TypeError, ValueError):
                            pass
        except Exception:
            pass

        # 资产负债率
        try:
            fin_abstract = ak.stock_financial_abstract(symbol=symbol)
            if fin_abstract is not None and not fin_abstract.empty:
                latest = fin_abstract.iloc[0]
                for col in ["资产负债率(%)", "资产负债率"]:
                    if col in fin_abstract.columns and pd.notna(latest.get(col)):
                        try:
                            result["debt_ratio"] = float(latest[col])
                            break
                        except (TypeError, ValueError):
                            pass
        except Exception:
            pass

        fundamental_cache.set(cache_key, result, ttl=3600)
        return result
