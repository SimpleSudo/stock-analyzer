"""
A股分析系统 API 入口
- 所有同步分析函数通过 run_in_executor 包装，避免阻塞事件循环
- 使用 APIRouter 实现版本控制（/api/v1/...）
- 集成 WebSocket 实时行情推送
"""
import asyncio
import json
import logging
import os
import threading
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter
from pydantic import BaseModel

# 自动加载项目根目录 .env 文件
try:
    from dotenv import load_dotenv
    _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    load_dotenv(os.path.join(_base, ".env"), override=True)
except ImportError:
    pass

from utils.logger import setup_logging
setup_logging(os.getenv("LOG_LEVEL", "INFO"))

logger = logging.getLogger(__name__)

from .stock_analysis import get_analysis, get_full_analysis
from .symbol_resolver import resolve_symbol, search_stocks, preload_stock_list, get_stock_name
from agents.technical_agent import TechnicalAgent
from agents.fundamental_agent import FundamentalAgent
from agents.sentiment_agent import SentimentAgent
from agents.decision_committee import DecisionCommittee
from tools.toolkit import Toolkit
from backtest.engine import BacktestEngine
from data.history_store import HistoryStore
from data.watchlist_store import WatchlistStore

# ── FastAPI App ──────────────────────────────────────────

app = FastAPI(title="A股分析系统 API", version="2.0.0")

# CORS
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

# ── Singletons ───────────────────────────────────────────

toolkit = Toolkit()
technical_agent = TechnicalAgent(toolkit=toolkit)
fundamental_agent = FundamentalAgent(toolkit=toolkit)
sentiment_agent = SentimentAgent(toolkit=toolkit)
committee = DecisionCommittee(
    agents=[technical_agent, fundamental_agent, sentiment_agent],
    weights={"Technical": 0.5, "Fundamental": 0.3, "Sentiment": 0.2},
)
backtest_engine = BacktestEngine()
history_store = HistoryStore()
watchlist_store = WatchlistStore()

# 预加载股票列表
threading.Thread(target=preload_stock_list, daemon=True).start()

# ── 请求模型 ─────────────────────────────────────────────

class StockRequest(BaseModel):
    symbol: str

class BacktestRequest(BaseModel):
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: Optional[float] = 100000.0

class WatchlistAddRequest(BaseModel):
    symbol: str
    name: Optional[str] = None

class ChatRequest(BaseModel):
    question: str
    symbol: Optional[str] = None
    context: Optional[dict] = None

class PortfolioRequest(BaseModel):
    symbols: list[str]

class AlertRequest(BaseModel):
    symbol: str
    target_price: float
    direction: str = "above"  # "above" or "below"
    note: Optional[str] = None

# ── 辅助：在线程池中运行同步函数 ─────────────────────────

async def _run_sync(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)


# ══════════════════════════════════════════════════════════
#  API v1 Router
# ══════════════════════════════════════════════════════════

v1 = APIRouter(prefix="/api/v1")

# ── 核心分析 ─────────────────────────────────────────────

@v1.post("/analyze")
async def analyze_stock(request: StockRequest):
    """完整多维度股票分析"""
    try:
        symbol = resolve_symbol(request.symbol)
        stock_name = get_stock_name(request.symbol)
        result = await _run_sync(get_full_analysis, symbol, stock_name)
        if "error" in result and result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        # 保存到历史记录
        try:
            history_store.add(
                symbol=symbol,
                name=stock_name or symbol,
                signal=result.get("signal", ""),
                score=result.get("score", 0),
                price=result.get("data", {}).get("latest", {}).get("price", 0),
            )
        except Exception as e:
            logger.warning("保存分析历史失败: %s", e)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("分析失败 [%s]: %s", request.symbol, e)
        raise HTTPException(status_code=500, detail=str(e))

@v1.post("/analyze/technical")
async def analyze_technical(request: StockRequest):
    """仅技术面分析"""
    try:
        result = await _run_sync(technical_agent.analyze, request.symbol.strip())
        if "error" in result and result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return {
            "symbol": request.symbol.strip(),
            "data": result.get("data"),
            "indicators": result.get("indicators", {}),
            "signal": result.get("signal"),
            "score": result.get("score"),
            "reasons": result.get("reasons"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@v1.post("/analyze/fundamental")
async def analyze_fundamental(request: StockRequest):
    """仅基本面分析"""
    try:
        result = await _run_sync(fundamental_agent.analyze, request.symbol.strip())
        if "error" in result and result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return {
            "symbol": request.symbol.strip(),
            "indicators": result.get("indicators", {}),
            "signal": result.get("signal"),
            "score": result.get("score"),
            "reasons": result.get("reasons"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@v1.post("/analyze/committee")
async def analyze_committee(request: StockRequest):
    """决策委员会综合分析"""
    try:
        result = await _run_sync(committee.analyze, request.symbol.strip())
        if "error" in result and result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@v1.post("/analyze/debate")
async def analyze_debate(request: StockRequest):
    """多 Agent 辩论视图"""
    try:
        sym = request.symbol.strip()
        tech, fund, sent = await asyncio.gather(
            _run_sync(technical_agent.analyze, sym),
            _run_sync(fundamental_agent.analyze, sym),
            _run_sync(sentiment_agent.analyze, sym),
        )
        return {
            "symbol": sym,
            "agent_outputs": {
                "Technical": tech,
                "Fundamental": fund,
                "Sentiment": sent,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@v1.post("/analyze/similar")
async def analyze_similar(request: StockRequest):
    """基于向量检索的相似历史分析"""
    try:
        current = await _run_sync(technical_agent.analyze, request.symbol.strip())
        if "error" in current and current["error"]:
            raise HTTPException(status_code=400, detail=current["error"])
        similar = technical_agent.retrieve_similar_analyses(request.symbol.strip(), current, top_k=5)
        return {
            "symbol": request.symbol.strip(),
            "current_analysis": {
                "signal": current.get("signal"),
                "score": current.get("score"),
                "reasons": current.get("reasons"),
            },
            "similar_analyses": [
                {
                    "date": m.get("timestamp"),
                    "signal": m.get("data", {}).get("signal"),
                    "score": m.get("data", {}).get("score"),
                    "reasons": m.get("data", {}).get("reasons"),
                    "symbol": m.get("symbol"),
                }
                for m in similar
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── 搜索 ─────────────────────────────────────────────────

@v1.get("/search")
async def search_stock(q: str = Query(default="", description="搜索关键词")):
    results = search_stocks(q, limit=10)
    return {"results": results}

# ── 回测 ─────────────────────────────────────────────────

@v1.post("/backtest/run")
async def run_backtest(request: BacktestRequest):
    """运行策略回测"""
    try:
        symbol = resolve_symbol(request.symbol)
        end_date = request.end_date or datetime.now().strftime("%Y%m%d")
        start_date = request.start_date or (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        start_date = start_date.replace("-", "")
        end_date = end_date.replace("-", "")
        result = await _run_sync(backtest_engine.run_backtest, symbol, start_date, end_date)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── 分析历史 ─────────────────────────────────────────────

@v1.get("/history")
async def get_history(
    symbol: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
):
    """获取分析历史记录"""
    return {"records": history_store.get_all(symbol=symbol, limit=limit)}

# ── 自选股 ───────────────────────────────────────────────

@v1.get("/watchlist")
async def get_watchlist():
    return {"watchlist": watchlist_store.get_all()}

@v1.post("/watchlist")
async def add_to_watchlist(request: WatchlistAddRequest):
    name = request.name
    if not name:
        name = get_stock_name(request.symbol) or request.symbol
    watchlist_store.add(request.symbol, name)
    return {"status": "ok", "symbol": request.symbol, "name": name}

@v1.delete("/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str):
    watchlist_store.remove(symbol)
    return {"status": "ok", "symbol": symbol}

# ── 组合分析 ─────────────────────────────────────────────

@v1.post("/analyze/portfolio")
async def analyze_portfolio(request: PortfolioRequest):
    """多股票组合分析"""
    from .portfolio_analysis import analyze_portfolio as _analyze
    try:
        symbols = [resolve_symbol(s) for s in request.symbols[:10]]
        result = await _run_sync(_analyze, symbols)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── AI 对话 ──────────────────────────────────────────────

@v1.post("/ai/chat")
async def ai_chat(request: ChatRequest):
    """AI 对话式分析"""
    from .llm_reporter import _build_chat_response
    try:
        response = await _run_sync(
            _build_chat_response,
            request.question,
            request.symbol,
            request.context,
        )
        return {"reply": response}
    except Exception as e:
        logger.error("AI 对话失败: %s", e)
        return {"reply": f"抱歉，AI 分析暂时不可用：{e}"}

# ── 告警 ─────────────────────────────────────────────────

@v1.post("/alerts")
async def create_alert(request: AlertRequest):
    from alerts.alert_manager import alert_manager
    alert_id = alert_manager.add(
        symbol=request.symbol,
        target_price=request.target_price,
        direction=request.direction,
        note=request.note,
    )
    return {"status": "ok", "alert_id": alert_id}

@v1.get("/alerts")
async def get_alerts(symbol: Optional[str] = None):
    from alerts.alert_manager import alert_manager
    return {"alerts": alert_manager.get_all(symbol=symbol)}

@v1.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    from alerts.alert_manager import alert_manager
    alert_manager.remove(alert_id)
    return {"status": "ok"}

# ── 健康检查 ─────────────────────────────────────────────

@v1.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}


# ══════════════════════════════════════════════════════════
#  注册路由（同时挂载 /api/ 和 /api/v1/ 以保持向后兼容）
# ══════════════════════════════════════════════════════════

app.include_router(v1)

# 向后兼容：/api/... → 映射到 v1 的同名路径
compat = APIRouter(prefix="/api")

@compat.get("/")
async def root():
    return {"message": "A股分析系统 API v2.0"}

@compat.post("/analyze")
async def compat_analyze(request: StockRequest):
    return await analyze_stock(request)

@compat.get("/health")
async def compat_health():
    return await health_check()

@compat.get("/search")
async def compat_search(q: str = Query(default="")):
    return await search_stock(q)

@compat.post("/analyze/technical")
async def compat_technical(request: StockRequest):
    return await analyze_technical(request)

@compat.post("/analyze/fundamental")
async def compat_fundamental(request: StockRequest):
    return await analyze_fundamental(request)

@compat.post("/analyze/committee")
async def compat_committee(request: StockRequest):
    return await analyze_committee(request)

@compat.post("/analyze/debate")
async def compat_debate(request: StockRequest):
    return await analyze_debate(request)

@compat.post("/analyze/similar")
async def compat_similar(request: StockRequest):
    return await analyze_similar(request)

@compat.post("/backtest/run")
async def compat_backtest(request: BacktestRequest):
    return await run_backtest(request)

app.include_router(compat)


# ══════════════════════════════════════════════════════════
#  WebSocket 实时行情
# ══════════════════════════════════════════════════════════

@app.websocket("/ws/realtime/{symbol}")
async def websocket_realtime(websocket: WebSocket, symbol: str):
    """WebSocket 实时行情推送（每 5 秒一次）"""
    await websocket.accept()
    logger.info("WebSocket 连接: %s", symbol)
    try:
        while True:
            try:
                quote = await _run_sync(toolkit.akshare.get_stock_realtime_quote, symbol)
                if quote:
                    await websocket.send_json(quote)
            except Exception as e:
                logger.debug("实时行情获取失败: %s", e)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info("WebSocket 断开: %s", symbol)
    except Exception as e:
        logger.warning("WebSocket 异常: %s", e)


# ── 入口 ─────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
