from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from typing import Optional, List

class BacktestRequest(BaseModel):
    token: str = Field(..., example="1", description="Instrument token")
    from_date: date = Field(..., description="Start date (YYYY-MM-DD or ISO datetime)")
    to_date: date = Field(..., description="End date (YYYY-MM-DD or ISO datetime)")
    quantity: float = Field(default=1, gt=0, example=50)

    @validator('from_date', 'to_date', pre=True)
    def parse_date(cls, value):
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.date()
            except ValueError:
                try:
                    return datetime.strptime(value, "%Y-%m-%d").date()
                except ValueError:
                    raise ValueError("Invalid date format. Use YYYY-MM-DD or ISO datetime.")
        return value

class Trade(BaseModel):
    trade_id: str
    symbol: str
    strategy_name: str
    quantity: float
    entry_time: datetime
    entry_price: float
    stop_loss: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    gross_pnl: Optional[float] = None
    brokerage: float = 0.0
    net_pnl: Optional[float] = None
    exit_reason: Optional[str] = None

class Metrics(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    net_profit: float
    gross_profit: float
    gross_loss: float
    average_profit: float
    average_loss: float
    largest_profit: float
    largest_loss: float
    max_drawdown: float
    profit_factor: float

class BacktestResponse(BaseModel):
    symbol: str
    token: str
    from_date: date
    to_date: date
    strategy: str
    total_candles: int
    trades: List[Trade]
    metrics: Metrics

class ErrorResponse(BaseModel):
    detail: str

class HealthResponse(BaseModel):
    status: str
    database: str
    version: str