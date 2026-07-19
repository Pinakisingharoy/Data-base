from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from zoneinfo import ZoneInfo
import repository

UTC = ZoneInfo("UTC")
IST = ZoneInfo("Asia/Kolkata")

@dataclass
class Candle:
    exchange_time: datetime
    open: float
    high: float
    low: float
    close: float

class CandleBuilder:
    def __init__(self):
        self.ticks: List[Dict] = []
        self.candles: List[Candle] = []

    def load_ticks(self, token: str, from_dt: datetime, to_dt: datetime):
        self.ticks = repository.fetch_ticks(token, from_dt, to_dt)
        if not self.ticks:
            raise ValueError("No tick data found.")
        return self.ticks

    @staticmethod
    def validate_tick(raw: Dict) -> bool:
        required = ["o", "h", "l", "c"]
        for key in required:
            if key not in raw or raw[key] in ("", None, "0", 0):
                return False
        return True

    @staticmethod
    def parse_tick(row: Dict) -> Optional[Dict]:
        raw = row["raw_data"]
        if not CandleBuilder.validate_tick(raw):
            return None
        try:
            ex_time = row["exchange_time"]
            if ex_time.tzinfo is None:
                ex_time = ex_time.replace(tzinfo=UTC)
            ex_time = ex_time.astimezone(IST)
            return {
                "exchange_time": ex_time,
                "open": float(raw["o"]),
                "high": float(raw["h"]),
                "low": float(raw["l"]),
                "close": float(raw["c"])
            }
        except Exception:
            return None

    def parsed_ticks(self) -> List[Dict]:
        parsed = []
        for row in self.ticks:
            tick = self.parse_tick(row)
            if tick:
                parsed.append(tick)
        parsed.sort(key=lambda x: x["exchange_time"])
        return parsed

    @staticmethod
    def floor_to_minute(dt: datetime) -> datetime:
        return dt.replace(second=0, microsecond=0)

    @staticmethod
    def create_candle(minute: datetime, first_price: float) -> Candle:
        return Candle(
            exchange_time=minute,
            open=first_price,
            high=first_price,
            low=first_price,
            close=first_price
        )

    @staticmethod
    def update_candle(candle: Candle, tick: Dict):
        candle.high = max(candle.high, tick["high"])
        candle.low = min(candle.low, tick["low"])
        candle.close = tick["close"]

    def build_candles(self) -> List[Candle]:
        ticks = self.parsed_ticks()
        if not ticks:
            raise ValueError("No valid ticks found.")
        self.candles = []
        current_minute = None
        current_candle = None

        for tick in ticks:
            minute = self.floor_to_minute(tick["exchange_time"])
            if current_candle is None:
                current_minute = minute
                current_candle = self.create_candle(minute, tick["open"])
                self.update_candle(current_candle, tick)
                continue

            if minute == current_minute:
                self.update_candle(current_candle, tick)
            else:
                self.candles.append(current_candle)
                current_minute = minute
                current_candle = self.create_candle(minute, tick["open"])
                self.update_candle(current_candle, tick)

        if current_candle:
            self.candles.append(current_candle)
        return self.candles

    def build(self, token: str, from_dt: datetime, to_dt: datetime, fill_gaps=False):
        self.load_ticks(token, from_dt, to_dt)
        self.build_candles()
        return self.candles