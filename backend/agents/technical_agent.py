from .base_agent import BaseAgent
from src.stock_analysis import get_analysis

class TechnicalAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("Technical", llm)

    def analyze(self, symbol: str) -> dict:
        """
        Perform technical analysis on the given stock symbol.
        Returns a dict compatible with the decision committee expectations.
        """
        # Get the analysis from the existing stock analysis function
        result = get_analysis(symbol)
        
        # If there was an error, return a neutral signal with error info
        if "error" in result:
            return {
                "agent": self.name,
                "score": 0,
                "signal": "错误",
                "reasons": [result["error"]],
                "indicators": {},
                "data": None
            }
        
        # Extract the relevant parts for the agent's output
        return {
            "agent": self.name,
            "score": result["score"],
            "signal": result["signal"],
            "reasons": result["reasons"],
            "indicators": result["indicators"],
            "data": result["data"]  # Optional: include raw data if needed by others
        }