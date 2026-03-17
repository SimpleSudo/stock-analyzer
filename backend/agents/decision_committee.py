from typing import List, Dict, Any, Optional
from .base_agent import BaseAgent

class DecisionCommittee:
    def __init__(self, agents: List[BaseAgent], weights: Optional[Dict[str, float]] = None):
        """
        Initialize the decision committee with a list of agents.
        :param agents: List of agent instances (e.g., TechnicalAgent, FundamentalAgent)
                       The first agent is expected to provide data and indicators for charting.
        :param weights: Optional dictionary mapping agent name to weight (float). 
                        If not provided, equal weights are used.
        """
        self.agents = agents
        if weights is None:
            # Equal weights
            self.weights = {agent.name: 1.0 for agent in agents}
        else:
            self.weights = weights
        # Normalize weights to sum to 1 (optional, but we can keep as is and just compute weighted sum)
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

    def analyze(self, symbol: str) -> Dict[str, Any]:
        """
        Get analysis from each agent and combine them.
        Returns a dict that matches the structure of the original get_analysis:
        {
            "symbol": str,
            "data": {
                "latest": {...},
                "chart": [...]
            },
            "indicators": {...},
            "signal": str,
            "score": float,
            "reasons": List[str]
        }
        The data and indicators are taken from the first agent (assumed to be the technical agent).
        """
        if not self.agents:
            return {
                "symbol": symbol,
                "error": "No agents in committee",
                "data": None,
                "indicators": {},
                "signal": "错误",
                "score": 0,
                "reasons": ["委员会中没有代理人"]
            }

        # Get output from each agent
        agent_outputs = []
        for agent in self.agents:
            output = agent.analyze(symbol)
            agent_outputs.append(output)

        # We'll use the first agent's data and indicators for the frontend charting and latest price
        primary_output = agent_outputs[0]
        # If the primary output has an error, we might still want to show something? We'll let the error propagate via the primary output's error field.
        # For now, we assume the primary agent (technical) works.

        # Compute weighted score and collect reasons
        weighted_score_sum = 0.0
        all_reasons = []

        for i, agent in enumerate(self.agents):
            output = agent_outputs[i]
            weight = self.weights.get(agent.name, 1.0)
            score = output.get("score", 0)
            weighted_score_sum += weight * score
            reasons = output.get("reasons", [])
            if isinstance(reasons, list):
                all_reasons.extend([f"[{agent.name}] {r}" for r in reasons])
            else:
                all_reasons.append(f"[{agent.name}] {reasons}")

        # Determine signal based on weighted score
        signal = self._score_to_signal(weighted_score_sum)

        # Build the result in the expected format
        result = {
            "symbol": symbol,
            "data": primary_output.get("data"),  # This should be the dict with latest and chart
            "indicators": primary_output.get("indicators", {}),
            "signal": signal,
            "score": round(weighted_score_sum, 2),
            "reasons": all_reasons
        }

        # If the primary output had an error, we might want to include it? 
        # For now, we'll just return the result as is. The primary output's error would be in its own field, but we are not including that.
        # We could add an error field if the primary output had one, but let's keep it simple for now.
        # If you want to propagate error, you can check primary_output.get("error") and then return an error structure.

        return result

    def _score_to_signal(self, score: float) -> str:
        """
        Convert a numeric score to a signal string.
        Adjust thresholds as needed.
        """
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