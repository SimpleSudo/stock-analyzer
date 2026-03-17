from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAgent(ABC):
    def __init__(self, name: str, llm=None):
        self.name = name
        self.llm = llm  # Can be injected later for LLM-powered agents

    @abstractmethod
    def analyze(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze the given stock symbol.
        Returns a dictionary with at least:
        - agent: str (name of this agent)
        - score: float (e.g., -10 to +10)
        - signal: str (e.g., "买入", "卖出", "观望")
        - reasons: List[str] (list of reasons for the decision)
        Optional fields can include indicators, confidence, etc.
        """
        pass

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Placeholder for tool calling mechanism.
        In a full implementation, this would interact with a tool registry.
        For now, agents can directly import and use tools.
        """
        # This is a stub; actual implementation will depend on toolkit design
        raise NotImplementedError("Tool calling not implemented in base agent")