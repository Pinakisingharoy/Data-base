from typing import List, Tuple
import config
from candle_builder import Candle

class Strategy:
    def __init__(self, lookback: int = config.BREAKOUT_CANDLES):
        self.lookback = lookback

    def check_entry(self, candles: List[Candle], index: int) -> Tuple[bool, float]:
        if index < self.lookback:
            return False, 0.0
        prev = candles[index - self.lookback : index]
        highest_close = max(c.close for c in prev)
        current = candles[index]
        if current.close > highest_close:
            return True, highest_close
        return False, 0.0