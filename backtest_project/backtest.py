from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import uuid
import config
import db
import schemas

IST = timezone(timedelta(hours=5, minutes=30))

def fetch_candles_and_symbol(token: str, from_date: datetime, to_date: datetime) -> tuple[List[Dict], str]:
    query = """
        SELECT 
            exchange_time AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata' AS exchange_time_ist,
            raw_data,
            trading_symbol
        FROM backtest_data
        WHERE token = %s AND exchange_time BETWEEN %s AND %s
        ORDER BY exchange_time
    """
    rows = db.fetch_all(query, (token, from_date, to_date))
    if not rows:
        raise ValueError("No data found for the given token and date range.")

    trading_symbol = rows[0]['trading_symbol']
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
        if o == 0 or h == 0 or l == 0 or c == 0:
            continue
        ex_time = row['exchange_time_ist']
        if ex_time.tzinfo is None:
            ex_time = ex_time.replace(tzinfo=IST)
        candles.append({
            'exchange_time': ex_time,
            'open': o,
            'high': h,
            'low': l,
            'close': c
        })

    if len(candles) < 11:
        raise ValueError(f"Not enough valid candles (found {len(candles)}, need at least 11)")
    return candles, trading_symbol


def run_backtest(token: str, from_date: datetime, to_date: datetime, quantity: float = 1.0) -> schemas.BacktestResponse:
    candles, symbol = fetch_candles_and_symbol(token, from_date, to_date)

    trades = []
    in_position = False
    entry_price = 0.0
    entry_time = None
    current_sl = 0.0
    trade_data = None

    for i in range(10, len(candles)):
        current = candles[i]
        prev_10 = candles[i-10:i]
        highest_close = max(c['close'] for c in prev_10)

        # Debug: show why no entry
        print(f"[DEBUG] Candle {i}: close={current['close']}, highest_close={highest_close}")

        if not in_position:
            if current['close'] > highest_close:
                in_position = True
                entry_price = current['close']
                entry_time = current['exchange_time']
                current_sl = candles[i-1]['low']
                trade_data = {
                    'trade_id': str(uuid.uuid4()),
                    'symbol': symbol,
                    'strategy_name': config.STRATEGY_NAME,
                    'quantity': quantity,
                    'entry_time': entry_time,
                    'entry_price': entry_price,
                    'stop_loss': current_sl,
                    'exit_time': None,
                    'exit_price': None,
                    'gross_pnl': None,
                    'brokerage': config.BROKERAGE,
                    'net_pnl': None,
                    'exit_reason': None,
                }
                print(f"[ENTRY] {entry_time} price={entry_price} SL={current_sl}")
                continue

        else:
            if current['low'] <= current_sl or current['close'] <= current_sl:
                exit_price = current_sl
                exit_time = current['exchange_time']
                gross_pnl = (exit_price - entry_price) * quantity
                net_pnl = gross_pnl - config.BROKERAGE

                trade_data['exit_time'] = exit_time
                trade_data['exit_price'] = exit_price
                trade_data['gross_pnl'] = gross_pnl
                trade_data['net_pnl'] = net_pnl
                trade_data['exit_reason'] = 'stop_loss'
                trades.append(trade_data)
                print(f"[EXIT] {exit_time} price={exit_price} PnL={gross_pnl}")

                in_position = False
                trade_data = None
                continue

            if current['low'] > current_sl:
                current_sl = current['low']

    if in_position and trade_data:
        last_candle = candles[-1]
        exit_price = last_candle['close']
        exit_time = last_candle['exchange_time']
        gross_pnl = (exit_price - entry_price) * quantity
        net_pnl = gross_pnl - config.BROKERAGE
        trade_data['exit_time'] = exit_time
        trade_data['exit_price'] = exit_price
        trade_data['gross_pnl'] = gross_pnl
        trade_data['net_pnl'] = net_pnl
        trade_data['exit_reason'] = 'end_of_data'
        trades.append(trade_data)
        print(f"[FORCE EXIT] {exit_time} price={exit_price}")

    total_trades = len(trades)
    if total_trades == 0:
        metrics = schemas.Metrics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            net_profit=0.0,
            gross_profit=0.0,
            gross_loss=0.0,
            average_profit=0.0,
            average_loss=0.0,
            largest_profit=0.0,
            largest_loss=0.0,
            max_drawdown=0.0,
            profit_factor=0.0
        )
        trade_objs = []
    else:
        winners = [t for t in trades if t['gross_pnl'] > 0]
        losers = [t for t in trades if t['gross_pnl'] <= 0]
        winning_trades = len(winners)
        losing_trades = len(losers)

        gross_profit = sum(t['gross_pnl'] for t in winners)
        gross_loss = abs(sum(t['gross_pnl'] for t in losers))
        net_profit = sum(t['net_pnl'] for t in trades)

        win_rate = (winning_trades / total_trades) * 100 if total_trades else 0
        avg_profit = net_profit / total_trades
        avg_winner = gross_profit / winning_trades if winning_trades else 0
        avg_loser = -gross_loss / losing_trades if losing_trades else 0
        largest_winner = max((t['gross_pnl'] for t in winners), default=0)
        largest_loser = min((t['gross_pnl'] for t in losers), default=0)
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')

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

        metrics = schemas.Metrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=round(win_rate, 2),
            net_profit=round(net_profit, 2),
            gross_profit=round(gross_profit, 2),
            gross_loss=round(gross_loss, 2),
            average_profit=round(avg_profit, 2),
            average_loss=round(avg_loser, 2),
            largest_profit=round(largest_winner, 2),
            largest_loss=round(largest_loser, 2),
            max_drawdown=round(max_dd, 2),
            profit_factor=round(profit_factor, 2) if profit_factor != float('inf') else float('inf')
        )

        trade_objs = [schemas.Trade(**t) for t in trades]

    response = schemas.BacktestResponse(
        symbol=symbol,
        token=token,
        from_date=from_date.date(),
        to_date=to_date.date(),
        strategy=config.STRATEGY_NAME,
        total_candles=len(candles),
        trades=trade_objs,
        metrics=metrics
    )
    return response


def run_backtest_from_request(request: schemas.BacktestRequest) -> schemas.BacktestResponse:
    from_dt = datetime.combine(request.from_date, datetime.min.time())
    to_dt = datetime.combine(request.to_date, datetime.max.time())
    return run_backtest(request.token, from_dt, to_dt, request.quantity)