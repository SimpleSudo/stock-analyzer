from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import os

# 自动加载项目根目录 .env 文件（开发环境）
try:
    from dotenv import load_dotenv
    # 向上查找 .env（backend/src/main.py → backend/ → 项目根）
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    load_dotenv(os.path.join(_base, ".env"), override=True)
except ImportError:
    pass  # python-dotenv 未安装时跳过（生产环境通过系统环境变量注入）
from .stock_analysis import get_analysis, get_full_analysis
from .symbol_resolver import resolve_symbol, search_stocks, preload_stock_list, get_stock_name
from agents.technical_agent import TechnicalAgent
from agents.fundamental_agent import FundamentalAgent
from agents.sentiment_agent import SentimentAgent
from agents.decision_committee import DecisionCommittee
from tools.toolkit import Toolkit
from backtest.engine import BacktestEngine
import uvicorn

app = FastAPI(title="A股分析系统 API", version="1.0.0")

# CORS middleware - 从环境变量读取，避免硬编码内网 IP
_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StockRequest(BaseModel):
    symbol: str

class BacktestRequest(BaseModel):
    symbol: str
    start_date: Optional[str] = None  # format YYYYMMDD
    end_date: Optional[str] = None    # format YYYYMMDD
    initial_capital: Optional[float] = 100000.0

@app.get("/")
async def root():
    return {"message": "A股分析系统 API"}

@app.post("/api/analyze")
async def analyze_stock(request: StockRequest):
    """
    完整多维度股票分析：技术面 + 基本面 + 行业对比 + 资金流向 + 价格目标 + AI报告。
    支持输入 6 位代码（000001）或股票名称（平安银行、农产品）。
    """
    import asyncio
    try:
        symbol = resolve_symbol(request.symbol)
        stock_name = get_stock_name(request.symbol)  # 尽量传入中文名，供 LLM 使用
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, get_full_analysis, symbol, stock_name)
        if "error" in result and result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/search")
async def search_stock(q: str = Query(default="", description="搜索关键词（代码或名称）")):
    """
    模糊搜索股票，返回匹配的代码+名称列表（用于前端输入建议）
    """
    results = search_stocks(q, limit=10)
    return {"results": results}

# 应用启动时后台预加载股票列表（避免首次请求因网络拉取而慢）
import threading
threading.Thread(target=preload_stock_list, daemon=True).start()

# Initialize toolkit and agents (singleton)
toolkit = Toolkit()
technical_agent = TechnicalAgent(toolkit=toolkit)
fundamental_agent = FundamentalAgent(toolkit=toolkit)
sentiment_agent = SentimentAgent(toolkit=toolkit)  # New sentiment agent
# Example weights: you can adjust these as needed
committee = DecisionCommittee(
    agents=[technical_agent, fundamental_agent, sentiment_agent],
    weights={"Technical": 0.5, "Fundamental": 0.3, "Sentiment": 0.2}  # Example weights
)

# Initialize backtest engine (singleton)
backtest_engine = BacktestEngine()

@app.post("/api/analyze/technical")
async def analyze_technical(request: StockRequest):
    """
    Analyze a stock using only the technical agent
    """
    try:
        result = technical_agent.analyze(request.symbol.strip())
        if "error" in result and result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        # Return in the same format as the original analyze for compatibility
        return {
            "symbol": request.symbol.strip(),
            "data": result.get("data"),
            "indicators": result.get("indicators", {}),
            "signal": result.get("signal"),
            "score": result.get("score"),
            "reasons": result.get("reasons")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/fundamental")
async def analyze_fundamental(request: StockRequest):
    """
    Analyze a stock using only the fundamental agent
    """
    try:
        result = fundamental_agent.analyze(request.symbol.strip())
        if "error" in result and result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return {
            "symbol": request.symbol.strip(),
            "data": result.get("data"),
            "indicators": result.get("indicators", {}),
            "signal": result.get("signal"),
            "score": result.get("score"),
            "reasons": result.get("reasons")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/committee")
async def analyze_committee(request: StockRequest):
    """
    Analyze a stock using the decision committee (multiple agents)
    """
    try:
        result = committee.analyze(request.symbol.strip())
        # The committee's analyze already returns the expected format
        if "error" in result and result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/similar")
async def analyze_similar(request: StockRequest):
    """
    Get similar historical analyses for a stock based on current technical/fundamental analysis.
    Returns list of similar past analyses with their outcomes.
    """
    try:
        # Use technical agent to get current analysis (could also use committee)
        current = technical_agent.analyze(request.symbol.strip())
        if "error" in current and current["error"]:
            raise HTTPException(status_code=400, detail=current["error"])
        # Retrieve similar analyses from vector store
        similar = technical_agent.retrieve_similar_analyses(request.symbol.strip(), current, top_k=5)
        # Format response
        return {
            "symbol": request.symbol.strip(),
            "current_analysis": {
                "signal": current.get("signal"),
                "score": current.get("score"),
                "reasons": current.get("reasons")
            },
            "similar_analyses": [
                {
                    "date": m.get("timestamp"),
                    "signal": m.get("data", {}).get("signal"),
                    "score": m.get("data", {}).get("score"),
                    "reasons": m.get("data", {}).get("reasons"),
                    "symbol": m.get("symbol")
                }
                for m in similar
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/debate")
async def analyze_debate(request: StockRequest):
    """
    Get analysis from each agent in the committee for transparency (debate view).
    Returns each agent's raw output.
    """
    try:
        # We need to get the raw agent outputs from the committee.
        # Let's modify the committee to have a method that returns agent outputs without combining.
        # For now, we can call each agent individually.
        technical_result = technical_agent.analyze(request.symbol.strip())
        fundamental_result = fundamental_agent.analyze(request.symbol.strip())
        sentiment_result = sentiment_agent.analyze(request.symbol.strip())
        return {
            "symbol": request.symbol.strip(),
            "agent_outputs": {
                "Technical": technical_result,
                "Fundamental": fundamental_result,
                "Sentiment": sentiment_result,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backtest/run")
async def run_backtest(request: BacktestRequest):
    """
    Run a backtest for the given symbol.
    Accepts JSON: {"symbol": "000001", "start_date": "20240101", "end_date": "20241231", "initial_capital": 100000}
    """
    try:
        symbol = resolve_symbol(request.symbol)
        end_date = request.end_date or datetime.now().strftime('%Y%m%d')
        start_date = request.start_date or (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        # 统一去掉日期中的连字符，兼容 "2024-01-01" 和 "20240101" 两种格式
        start_date = start_date.replace('-', '')
        end_date = end_date.replace('-', '')

        result = backtest_engine.run_backtest(symbol, start_date, end_date)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
