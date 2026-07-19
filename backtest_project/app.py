from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import config
import db
from schemas import (
    BacktestRequest,
    BacktestResponse,
    ErrorResponse,
    HealthResponse
)
from backtest import run_backtest_from_request

app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description=config.APP_DESCRIPTION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    db.initialize_connection_pool()
    print("Application started.")

@app.on_event("shutdown")
def shutdown():
    db.close_pool()
    print("Application shut down.")

@app.get("/", response_model=HealthResponse)
async def root():
    try:
        result = db.fetch_one("SELECT version()")
        db_ok = "PostgreSQL" in result.get("version", "")
        status = "healthy" if db_ok else "degraded"
    except Exception:
        db_ok = False
        status = "unhealthy"
    return HealthResponse(
        status=status,
        database="connected" if db_ok else "disconnected",
        version=config.APP_VERSION
    )

@app.post(
    "/backtest",
    response_model=BacktestResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def backtest(request: BacktestRequest):
    try:
        return run_backtest_from_request(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=config.DEBUG)