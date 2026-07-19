from datetime import datetime
from typing import List, Dict, Optional
import db

def fetch_ticks(token: str, from_dt: datetime, to_dt: datetime) -> List[Dict]:
    query = """
        SELECT
            exchange_time,
            raw_data,
            trading_symbol,
            token
        FROM backtest_data
        WHERE token = %s
          AND exchange_time BETWEEN %s AND %s
        ORDER BY exchange_time ASC
    """
    return db.fetch_all(query, (token, from_dt, to_dt))

def fetch_symbol(token: str) -> Optional[str]:
    row = db.fetch_one(
        "SELECT trading_symbol FROM backtest_data WHERE token=%s LIMIT 1",
        (token,)
    )
    return row["trading_symbol"] if row else None