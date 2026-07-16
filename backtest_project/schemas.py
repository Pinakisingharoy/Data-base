from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# class BacktestRequest(BaseModel):
#     token: str
#     from_date: date
#     to_date: date
#     quantity: float = 1.0
class BacktestRequest(BaseModel):
    token: str = Field(
        ...,
        example="26000",
        description="Instrument Token"
    )

    from_date: date = Field(
        ...,
        example="2026-06-29"
    )

    to_date: date = Field(
        ...,
        example="2026-06-29"
    )

    quantity: float = Field(
        default=1,
        example=50
    )

class Trade(BaseModel):
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    quantity: float
    gross_pnl: Optional[float] = None
    net_pnl: Optional[float] = None
    exit_reason: Optional[str] = None
    symbol: str
    strategy_name: str

class BacktestResponse(BaseModel):
    trades: List[Trade]
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    net_profit: float
    average_profit: float
    max_drawdown: float
    profit_factor: float