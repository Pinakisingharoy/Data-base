import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Any
import db
import schemas

def fetch_candles(token: str, from_date: datetime, to_date: datetime) -> List[Dict[str, Any]]:
    """Fetch historical candle data from the raw_data JSONB field."""
    conn = db.get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT exchange_time, raw_data
        FROM backtest_data
        WHERE token = %s AND exchange_time BETWEEN %s AND %s
        ORDER BY exchange_time
    """
    cursor.execute(query, (token, from_date, to_date))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    candles = []
    for row in rows:
        raw = row['raw_data']
        try:
            o = float(raw.get('o', 0))
            h = float(raw.get('h', 0))
            l = float(raw.get('l', 0))
            c = float(raw.get('c', 0))
        except (TypeError, ValueError):
            continue
        candles.append({
            'exchange_time': row['exchange_time'],
            'open': o,
            'high': h,
            'low': l,
            'close': c
        })
    return candles

def run_backtest(token: str, from_date: datetime, to_date: datetime, quantity: float = 1.0) -> Dict:
    """
    Execute the breakout strategy:
        - Long entry when close > highest close of previous 10 candles.
        - Initial SL = low of candle before entry.
        - Trail SL upwards with each new candle's low.
        - Exit when price <= SL (or candle low <= SL).
    """
    candles = fetch_candles(token, from_date, to_date)
    if len(candles) < 11:
        raise ValueError("Not enough data (need at least 11 candles)")

    trades = []
    in_position = False
    entry_price = 0.0
    entry_time = None
    current_sl = 0.0
    trade = None

    for i in range(10, len(candles)):
        current = candles[i]
        prev_10 = candles[i-10:i]
        highest_close = max(c['close'] for c in prev_10)

        if not in_position:
            if current['close'] > highest_close:
                in_position = True
                entry_price = current['close']
                entry_time = current['exchange_time']
                current_sl = candles[i-1]['low']

                trade = {
                    'entry_time': entry_time,
                    'entry_price': entry_price,
                    'quantity': quantity,
                    'symbol': token,
                    'strategy_name': '10_breakout',
                    'exit_time': None,
                    'exit_price': None,
                    'gross_pnl': None,
                    'net_pnl': None,
                    'exit_reason': None,
                }
                continue

        else:
            if current['low'] <= current_sl or current['close'] <= current_sl:
                exit_price = current_sl
                exit_time = current['exchange_time']
                gross_pnl = (exit_price - entry_price) * quantity

                trade['exit_time'] = exit_time
                trade['exit_price'] = exit_price
                trade['gross_pnl'] = gross_pnl
                trade['net_pnl'] = gross_pnl
                trade['exit_reason'] = 'stop_loss'
                trades.append(trade)

                in_position = False
                trade = None
                continue

            new_sl = current['low']
            if new_sl > current_sl:
                current_sl = new_sl

    if in_position and trade:
        last_candle = candles[-1]
        exit_price = last_candle['close']
        exit_time = last_candle['exchange_time']
        gross_pnl = (exit_price - entry_price) * quantity

        trade['exit_time'] = exit_time
        trade['exit_price'] = exit_price
        trade['gross_pnl'] = gross_pnl
        trade['net_pnl'] = gross_pnl
        trade['exit_reason'] = 'end_of_data'
        trades.append(trade)

    total_trades = len(trades)
    if total_trades == 0:
        return {
            'trades': [],
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'net_profit': 0.0,
            'average_profit': 0.0,
            'max_drawdown': 0.0,
            'profit_factor': 0.0
        }

    winning = sum(1 for t in trades if t['gross_pnl'] > 0)
    losing = sum(1 for t in trades if t['gross_pnl'] < 0)
    win_rate = winning / total_trades
    net_profit = sum(t['net_pnl'] for t in trades)
    avg_profit = net_profit / total_trades

    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in trades:
        cumulative += t['net_pnl']
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    gross_profit = sum(t['gross_pnl'] for t in trades if t['gross_pnl'] > 0)
    gross_loss = sum(t['gross_pnl'] for t in trades if t['gross_pnl'] < 0)
    profit_factor = gross_profit / abs(gross_loss) if gross_loss != 0 else float('inf')

    trade_models = [schemas.Trade(**t) for t in trades]

    return {
        'trades': trade_models,
        'total_trades': total_trades,
        'winning_trades': winning,
        'losing_trades': losing,
        'win_rate': win_rate,
        'net_profit': net_profit,
        'average_profit': avg_profit,
        'max_drawdown': max_dd,
        'profit_factor': profit_factor
    }