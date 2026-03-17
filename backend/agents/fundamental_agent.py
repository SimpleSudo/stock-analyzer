from .base_agent import BaseAgent
from src.stock_analysis import get_analysis

class FundamentalAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("Fundamental", llm)

    def analyze(self, symbol: str) -> dict:
        """
        Perform fundamental analysis on the given stock symbol.
        For now, we reuse the same analysis as a placeholder.
        In the future, this will fetch financial statements, valuation ratios, etc.
        """
        result = get_analysis(symbol)
        if "error" in result:
            return {
                "agent": self.name,
                "score": 0,
                "signal": "错误",
                "reasons": [result["error"]],
                "indicators": {},
                "data": None
            }
        # For demonstration, we could adjust score based on fundamentals.
        # Here we just return the same as technical for simplicity.
        return {
            "agent": self.name,
            "score": result["score"],  # placeholder
            "signal": result["signal"],
            "reasons": result["reasons"],
            "indicators": result["indicators"],
            "data": result["data"]
        }