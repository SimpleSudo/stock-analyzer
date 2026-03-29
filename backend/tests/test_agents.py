"""
Agent 返回格式验证测试
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest


class TestAgentOutputFormat:
    """验证各 Agent 返回的字典格式"""

    REQUIRED_KEYS = {"agent", "score", "signal", "reasons", "indicators"}

    def _validate_output(self, output: dict):
        for key in self.REQUIRED_KEYS:
            assert key in output, f"Missing key: {key}"
        assert isinstance(output["score"], (int, float))
        assert isinstance(output["signal"], str)
        assert isinstance(output["reasons"], list)
        assert isinstance(output["indicators"], dict)

    def test_decision_committee_score_to_signal(self):
        from agents.decision_committee import DecisionCommittee
        committee = DecisionCommittee(agents=[])
        assert committee._score_to_signal(5.0) == "强烈买入"
        assert committee._score_to_signal(2.0) == "买入"
        assert committee._score_to_signal(0.0) == "观望"
        assert committee._score_to_signal(-2.0) == "卖出"
        assert committee._score_to_signal(-5.0) == "强烈卖出"

    def test_decision_committee_no_agents(self):
        from agents.decision_committee import DecisionCommittee
        committee = DecisionCommittee(agents=[])
        result = committee.analyze("000001")
        assert "error" in result or result["signal"] == "错误"
