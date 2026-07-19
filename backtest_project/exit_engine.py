from candle_builder import Candle

class ExitEngine:
    def __init__(self, entry_price: float, initial_sl: float):
        self.entry_price = entry_price
        self.current_sl = initial_sl
        self.is_active = True

    def update(self, candle: Candle) -> bool:
        if candle.low > self.current_sl:
            self.current_sl = candle.low
            return True
        return False

    def check_exit(self, candle: Candle) -> bool:
        return candle.low <= self.current_sl or candle.close <= self.current_sl

    def get_exit_price(self) -> float:
        return self.current_sl