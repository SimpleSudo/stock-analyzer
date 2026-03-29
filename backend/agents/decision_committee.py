"""
决策委员会 - 汇总各 Agent 分析结果
- 加权评分
- 辩论机制：检测矛盾 → LLM 仲裁 → 输出一致性指数
"""
import logging
from typing import List, Dict, Any, Optional
from .base_agent import BaseAgent
from .debate_moderator import DebateModerator

logger = logging.getLogger(__name__)


class DecisionCommittee:
    def __init__(self, agents: List[BaseAgent], weights: Optional[Dict[str, float]] = None):
        self.agents = agents
        if weights is None:
            self.weights = {agent.name: 1.0 for agent in agents}
        else:
            self.weights = weights
        # 归一化权重
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
        self.moderator = DebateModerator()

    def analyze(self, symbol: str) -> Dict[str, Any]:
        if not self.agents:
            return {
                "symbol": symbol,
                "error": "No agents in committee",
                "data": None,
                "indicators": {},
                "signal": "错误",
                "score": 0,
                "reasons": ["委员会中没有代理人"],
            }

        # 收集各 Agent 分析结果
        agent_outputs = []
        for agent in self.agents:
            try:
                output = agent.analyze(symbol)
                agent_outputs.append(output)
            except Exception as e:
                logger.warning("Agent %s 分析失败: %s", agent.name, e)
                agent_outputs.append({
                    "agent": agent.name,
                    "score": 0,
                    "signal": "错误",
                    "reasons": [f"分析失败: {e}"],
                    "indicators": {},
                    "data": None,
                })

        # 第一个 Agent（技术面）提供图表数据
        primary_output = agent_outputs[0]

        # 加权评分
        weighted_score_sum = 0.0
        all_reasons = []
        for i, agent in enumerate(self.agents):
            output = agent_outputs[i]
            weight = self.weights.get(agent.name, 0)
            score = output.get("score", 0)
            weighted_score_sum += weight * score
            reasons = output.get("reasons", [])
            if isinstance(reasons, list):
                all_reasons.extend([f"[{agent.name}] {r}" for r in reasons])
            else:
                all_reasons.append(f"[{agent.name}] {reasons}")

        # 辩论机制
        debate_result = self.moderator.run_debate(symbol, agent_outputs, weighted_score_sum)

        # 使用辩论调整后的信号和评分（如果有）
        final_score = debate_result.get("adjusted_score") or weighted_score_sum
        final_signal = debate_result.get("adjusted_signal") or self._score_to_signal(weighted_score_sum)

        # 如果辩论有摘要，加入理由
        debate_summary = debate_result.get("debate_summary", "")
        consensus_score = debate_result.get("consensus_score", 1.0)

        if debate_summary and consensus_score < 1.0:
            all_reasons.insert(0, f"[辩论仲裁] {debate_summary}")

        result = {
            "symbol": symbol,
            "data": primary_output.get("data"),
            "indicators": primary_output.get("indicators", {}),
            "signal": final_signal,
            "score": round(final_score, 2),
            "reasons": all_reasons,
            "consensus_score": consensus_score,
            "debate_summary": debate_summary,
            "agent_details": [
                {
                    "agent": o.get("agent"),
                    "signal": o.get("signal"),
                    "score": o.get("score", 0),
                }
                for o in agent_outputs
            ],
        }

        return result

    def _score_to_signal(self, score: float) -> str:
        if score >= 3.0:
            return "强烈买入"
        elif score >= 1.0:
            return "买入"
        elif score <= -3.0:
            return "强烈卖出"
        elif score <= -1.0:
            return "卖出"
        else:
            return "观望"
