from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .stock_analysis import get_analysis
from agents.technical_agent import TechnicalAgent
from agents.fundamental_agent import FundamentalAgent
from agents.decision_committee import DecisionCommittee
from tools.toolkit import Toolkit
import uvicorn

app = FastAPI(title="A股分析系统 API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StockRequest(BaseModel):
    symbol: str

@app.get("/")
async def root():
    return {"message": "A股分析系统 API"}

@app.post("/api/analyze")
async def analyze_stock(request: StockRequest):
    """
    Analyze a stock and return technical indicators and signals
    """
    try:
        result = get_analysis(request.symbol.strip())
        if "error" in result and result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Initialize toolkit and agents (singleton)
toolkit = Toolkit()
technical_agent = TechnicalAgent(toolkit=toolkit)
fundamental_agent = FundamentalAgent(toolkit=toolkit)
# Example weights: you can adjust these as needed
committee = DecisionCommittee(
    agents=[technical_agent, fundamental_agent],
    weights={"Technical": 0.6, "Fundamental": 0.4}  # Example: technical slightly more important
)

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
        # If you have more agents, add them here.
        return {
            "symbol": request.symbol.strip(),
            "agent_outputs": {
                "Technical": technical_result,
                "Fundamental": fundamental_result
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
