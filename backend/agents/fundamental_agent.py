from .base_agent import BaseAgent
from src.stock_analysis import get_analysis
import time

class FundamentalAgent(BaseAgent):
    def __init__(self, llm=None, toolkit=None):
        super().__init__("Fundamental", llm, toolkit)

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
        analysis_output = {
            "agent": self.name,
            "score": result["score"],  # placeholder
            "signal": result["signal"],
            "reasons": result["reasons"],
            "indicators": result["indicators"],
            "data": result["data"]
        }
        # Store this analysis in vector store for future similarity search
        try:
            self.store_analysis(symbol, analysis_output)
        except Exception as e:
            print(f"Warning: Failed to store analysis in vector store: {e}")
        return analysis_output