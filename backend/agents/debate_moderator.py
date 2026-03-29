"""
辩论主持人 - 检测 Agent 间信号矛盾并通过 LLM 仲裁
- 当多个 Agent 信号方向矛盾时启动辩论
- 输出一致性指数 (consensus_score) 和辩论摘要
- 无 LLM 时降级为规则仲裁
"""
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def _signal_direction(signal: str) -> int:
    """将信号映射为方向：+1 买入，-1 卖出，0 中性"""
    if "买入" in signal:
        return 1
    if "卖出" in signal:
        return -1
    return 0


class DebateModerator:
    """辩论主持人"""

    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            try:
                from llm.factory import LLMFactory
                self._llm = LLMFactory.create_llm()
            except Exception:
                self._llm = None
        return self._llm

    def detect_conflict(self, agent_outputs: List[Dict[str, Any]]) -> bool:
        """检测是否存在信号方向矛盾"""
        directions = set()
        for output in agent_outputs:
            sig = output.get("signal", "观望")
            d = _signal_direction(sig)
            if d != 0:
                directions.add(d)
        # 同时存在买入和卖出方向才算矛盾
        return len(directions) > 1

    def calculate_consensus(self, agent_outputs: List[Dict[str, Any]]) -> float:
        """
        计算一致性指数 0~1
        1.0 = 所有 Agent 方向一致
        0.0 = 完全矛盾
        """
        if not agent_outputs:
            return 1.0
        directions = [_signal_direction(o.get("signal", "观望")) for o in agent_outputs]
        # 过滤掉中性
        non_neutral = [d for d in directions if d != 0]
        if not non_neutral:
            return 0.5  # 全中性

        pos = sum(1 for d in non_neutral if d > 0)
        neg = sum(1 for d in non_neutral if d < 0)
        total = len(non_neutral)
        # 一致性 = 多数派比例
        return round(max(pos, neg) / total, 2)

    def run_debate(
        self,
        symbol: str,
        agent_outputs: List[Dict[str, Any]],
        weighted_score: float,
    ) -> Dict[str, Any]:
        """
        运行辩论流程。
        返回: {
            consensus_score: float,  # 0~1
            debate_summary: str,     # 辩论摘要
            adjusted_signal: str,    # 调整后的信号
            adjusted_score: float,   # 调整后的评分
        }
        """
        consensus = self.calculate_consensus(agent_outputs)
        has_conflict = self.detect_conflict(agent_outputs)

        if not has_conflict:
            return {
                "consensus_score": consensus,
                "debate_summary": "各分析维度方向一致，无需辩论。",
                "adjusted_signal": None,  # 无需调整
                "adjusted_score": None,
            }

        # 有矛盾，尝试 LLM 辩论
        llm = self._get_llm()
        if llm is not None and llm.is_available():
            return self._llm_debate(symbol, agent_outputs, weighted_score, consensus, llm)
        else:
            return self._rule_debate(agent_outputs, weighted_score, consensus)

    def _llm_debate(
        self,
        symbol: str,
        agent_outputs: List[Dict[str, Any]],
        weighted_score: float,
        consensus: float,
        llm,
    ) -> Dict[str, Any]:
        """LLM 驱动的辩论仲裁"""
        # 构建辩论 prompt
        agent_summaries = []
        for output in agent_outputs:
            name = output.get("agent", "Unknown")
            signal = output.get("signal", "观望")
            score = output.get("score", 0)
            reasons = output.get("reasons", [])
            reasons_text = "\n".join(f"  - {r}" for r in reasons[:5])
            agent_summaries.append(
                f"**{name} Agent** — 信号: {signal} (评分 {score})\n{reasons_text}"
            )

        debate_text = "\n\n".join(agent_summaries)
        prompt = (
            f"你是一位资深投资分析委员会的主席。以下是各分析 Agent 对股票 {symbol} 的独立分析结果，"
            f"它们之间存在信号矛盾：\n\n{debate_text}\n\n"
            f"加权综合评分: {weighted_score:.2f}\n"
            f"一致性指数: {consensus}\n\n"
            f"请作为仲裁者：\n"
            f"1. 分析各方论据的合理性\n"
            f"2. 指出哪些因素更有决定性\n"
            f"3. 给出最终建议信号（强烈买入/买入/观望/卖出/强烈卖出）\n"
            f"4. 用 2-3 句话总结你的判断理由\n\n"
            f"请直接给出分析，不要重复输入内容。"
        )

        try:
            response = llm.generate(prompt, max_tokens=500, temperature=0.3)
            # 从 LLM 回复中提取信号（简单匹配）
            adjusted_signal = None
            for sig in ["强烈买入", "强烈卖出", "买入", "卖出", "观望"]:
                if sig in response:
                    adjusted_signal = sig
                    break

            return {
                "consensus_score": consensus,
                "debate_summary": response.strip(),
                "adjusted_signal": adjusted_signal,
                "adjusted_score": weighted_score * consensus,  # 低一致性时降低评分
            }
        except Exception as e:
            logger.warning("LLM 辩论失败: %s", e)
            return self._rule_debate(agent_outputs, weighted_score, consensus)

    def _rule_debate(
        self,
        agent_outputs: List[Dict[str, Any]],
        weighted_score: float,
        consensus: float,
    ) -> Dict[str, Any]:
        """规则降级辩论：低一致性时评分打折、信号趋向观望"""
        adjusted_score = weighted_score * consensus

        # 矛盾严重时（consensus < 0.6）强制观望
        if consensus < 0.6:
            adjusted_signal = "观望"
            summary = (
                f"分析 Agent 间存在严重分歧（一致性 {consensus:.0%}），"
                f"建议暂时观望，等待更明确的信号。"
            )
        else:
            # 适度分歧，保留方向但降级强度
            if adjusted_score >= 1:
                adjusted_signal = "买入"
            elif adjusted_score <= -1:
                adjusted_signal = "卖出"
            else:
                adjusted_signal = "观望"
            summary = (
                f"分析 Agent 间存在一定分歧（一致性 {consensus:.0%}），"
                f"综合评分从 {weighted_score:.1f} 调整为 {adjusted_score:.1f}。"
            )

        return {
            "consensus_score": consensus,
            "debate_summary": summary,
            "adjusted_signal": adjusted_signal,
            "adjusted_score": round(adjusted_score, 2),
        }
