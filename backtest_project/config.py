import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "backtest")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")

BREAKOUT_CANDLES = 10
STRATEGY_NAME = "10_CANDLE_BREAKOUT"
DEFAULT_QUANTITY = 1
BROKERAGE = 0.0
SLIPPAGE = 0.0

APP_NAME = "Backtest API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "10 Candle Breakout Strategy Backtesting API"
DEBUG = True