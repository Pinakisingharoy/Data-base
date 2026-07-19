from dataclasses import dataclass
from typing import List
from schemas import Trade

@dataclass
class PerformanceMetrics:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    loss_rate: float
    gross_profit: float
    gross_loss: float
    net_profit: float
    average_profit: float
    average_winner: float
    average_loser: float
    largest_winner: float
    largest_loser: float
    profit_factor: float
    expectancy: float
    max_drawdown: float

class Metrics:
    @staticmethod
    def calculate(trades: List[Trade]) -> PerformanceMetrics:
        total = len(trades)
        if total == 0:
            return PerformanceMetrics(
                total_trades=0, winning_trades=0, losing_trades=0,
                win_rate=0, loss_rate=0, gross_profit=0, gross_loss=0,
                net_profit=0, average_profit=0, average_winner=0,
                average_loser=0, largest_winner=0, largest_loser=0,
                profit_factor=0, expectancy=0, max_drawdown=0
            )

        winners = [t for t in trades if t.net_pnl > 0]
        losers = [t for t in trades if t.net_pnl <= 0]
        winning_trades = len(winners)
        losing_trades = len(losers)

        gross_profit = sum(t.net_pnl for t in winners)
        gross_loss = abs(sum(t.net_pnl for t in losers))
        net_profit = sum(t.net_pnl for t in trades)

        avg_profit = net_profit / total
        avg_winner = gross_profit / winning_trades if winning_trades else 0
        avg_loser = -gross_loss / losing_trades if losing_trades else 0
        largest_winner = max((t.net_pnl for t in winners), default=0)
        largest_loser = min((t.net_pnl for t in losers), default=0)

        profit_factor = gross_profit / gross_loss if gross_loss != 0 else float("inf")
        win_rate = (winning_trades / total) * 100
        loss_rate = (losing_trades / total) * 100
        expectancy = net_profit / total

        equity = 0
        peak = 0
        max_dd = 0
        for t in trades:
            equity += t.net_pnl
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd

        return PerformanceMetrics(
            total_trades=total,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=round(win_rate, 2),
            loss_rate=round(loss_rate, 2),
            gross_profit=round(gross_profit, 2),
            gross_loss=round(gross_loss, 2),
            net_profit=round(net_profit, 2),
            average_profit=round(avg_profit, 2),
            average_winner=round(avg_winner, 2),
            average_loser=round(avg_loser, 2),
            largest_winner=round(largest_winner, 2),
            largest_loser=round(largest_loser, 2),
            profit_factor=round(profit_factor, 2) if profit_factor != float("inf") else float("inf"),
            expectancy=round(expectancy, 2),
            max_drawdown=round(max_dd, 2)
        )