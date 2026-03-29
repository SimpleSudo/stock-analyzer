"""
宏观经济 Agent
- 分析宏观环境对 A 股的影响
- 北向资金、Shibor、大盘趋势
"""
import logging
from .base_agent import BaseAgent
from src.macro_data import get_macro_indicators

logger = logging.getLogger(__name__)


class MacroAgent(BaseAgent):
    def __init__(self, llm=None, toolkit=None):
        super().__init__("Macro", llm, toolkit)

    def analyze(self, symbol: str) -> dict:
        try:
            macro = get_macro_indicators()
        except Exception as e:
            return {
                "agent": self.name, "score": 0, "signal": "观望",
                "reasons": [f"宏观数据获取失败: {e}"],
                "indicators": {}, "data": None,
            }

        score = 0
        reasons = []
        indicators = {}

        # 北向资金
        north_5d = macro.get("north_5day")
        if north_5d is not None:
            indicators["北向资金5日(亿)"] = north_5d
            if north_5d > 50:
                score += 2
                reasons.append(f"北向资金5日净流入 {north_5d:.0f} 亿，外资看多")
            elif north_5d > 0:
                score += 1
                reasons.append(f"北向资金5日净流入 {north_5d:.0f} 亿")
            elif north_5d < -50:
                score -= 2
                reasons.append(f"北向资金5日净流出 {abs(north_5d):.0f} 亿，外资撤退")
            else:
                score -= 1
                reasons.append(f"北向资金5日净流出 {abs(north_5d):.0f} 亿")

        # 大盘趋势
        sh_trend = macro.get("sh_trend")
        if sh_trend:
            indicators["大盘趋势"] = sh_trend
            if sh_trend == "上涨趋势":
                score += 1
                reasons.append("大盘处于上涨趋势（站上MA20）")
            else:
                score -= 1
                reasons.append("大盘处于下跌趋势（跌破MA20）")

        # Shibor
        shibor = macro.get("shibor_overnight")
        if shibor is not None:
            indicators["Shibor隔夜(%)"] = shibor
            if shibor < 1.5:
                score += 1
                reasons.append(f"Shibor隔夜 {shibor:.2f}%，流动性宽松")
            elif shibor > 2.5:
                score -= 1
                reasons.append(f"Shibor隔夜 {shibor:.2f}%，流动性偏紧")

        if not reasons:
            reasons.append("宏观数据不足，无法评估")

        signal = "买入" if score >= 2 else "卖出" if score <= -2 else "观望"

        return {
            "agent": self.name,
            "score": score,
            "signal": signal,
            "reasons": reasons,
            "indicators": indicators,
            "data": macro,
        }
