from fastapi import FastAPI, HTTPException
from datetime import datetime, time
import schemas
import backtest

app = FastAPI(title="Backtest API", description="Simple breakout strategy backtester")

@app.get("/")
async def root():
    return {"message": "Backtest API is running. Use POST /backtest"}

@app.post("/backtest", response_model=schemas.BacktestResponse)
async def backtest_endpoint(request: schemas.BacktestRequest):
    try:
        # Convert date-only to full datetime range for DB query
        from_datetime = datetime.combine(request.from_date, time.min)   # 00:00:00
        to_datetime   = datetime.combine(request.to_date, time.max)     # 23:59:59

        result = backtest.run_backtest(
            token=request.token,
            from_date=from_datetime,
            to_date=to_datetime,
            quantity=request.quantity
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")