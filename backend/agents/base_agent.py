import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

# Ensure the backend directory is in the path for absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)  # Go up to backend directory
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from tools.toolkit import Toolkit
from memory.vector_store import vector_store

class BaseAgent(ABC):
    def __init__(self, name: str, llm=None, toolkit: Optional[Toolkit] = None):
        self.name = name
        self.llm = llm  # Can be injected later for LLM-powered agents
        self.toolkit = toolkit or Toolkit()  # Default toolkit
        self.vector_store = vector_store  # Global vector store instance

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
        Call a tool by name.
        Currently only supports 'akshare' toolkit.
        """
        if tool_name == "akshare":
            return self.toolkit.akshare
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def store_analysis(self, symbol: str, analysis_data: Dict[str, Any]) -> str:
        """
        Store the analysis result in the vector store for future similarity search.
        Returns the storage ID.
        """
        # Add a timestamp if not present
        if 'timestamp' not in analysis_data:
            import time
            analysis_data['timestamp'] = int(time.time())
        return self.vector_store.add(symbol, analysis_data)

    def retrieve_similar_analyses(self, symbol: str, analysis_data: Dict[str, Any], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve similar historical analyses from the vector store.
        """
        return self.vector_store.search(symbol, analysis_data, top_k)