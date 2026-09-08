"""Backtesting engine for Robinhood Chain trading strategies.

Matches tweet params:
- pollIntervalMs, model, ctxCandles, thinkingBudget
- positionSizeEth, slippageBps, costPerDecision, dailyBurn
"""
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from rich.console import Console
from rich.table import Table
from rich.progress import track

from config import (
    POLL_INTERVAL_MS, MODEL, CTX_CANDLES, THINKING_BUDGET,
    POSITION_SIZE_ETH, SLIPPAGE_BPS, CHAIN_ID
)

console = Console()


@dataclass
class Trade:
    timestamp: datetime
    token: str
    side: str  # "buy" or "sell"
    price: float
    amount_eth: float
    amount_token: float
    slippage_bps: int
    fee_eth: float = 0.0
    pnl_eth: float = 0.0


@dataclass
class BacktestResult:
    start: datetime
    end: datetime
    trades: List[Trade] = field(default_factory=list)
    initial_eth: float = 0.0
    final_eth: float = 0.0
    total_pnl_eth: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    avg_slippage_bps: float = 0.0
    cost_per_decision: float = 0.0
    daily_burn: float = 0.0

    def summary(self) -> Dict:
        return {
            "period_days": (self.end - self.start).days,
            "initial_eth": round(self.initial_eth, 6),
            "final_eth": round(self.final_eth, 6),
            "pnl_eth": round(self.total_pnl_eth, 6),
            "pnl_pct": round((self.total_pnl_eth / self.initial_eth * 100) if self.initial_eth > 0 else 0, 2),
            "win_rate": round(self.win_rate * 100, 1),
            "trades": self.total_trades,
            "avg_slippage_bps": round(self.avg_slippage_bps, 1),
            "cost_per_decision_usd": round(self.cost_per_decision, 4),
            "daily_burn_usd": round(self.daily_burn, 2),
        }


class BacktestEngine:
    """Simulate trading decisions with configurable model params"""

    def __init__(
        self,
        initial_eth: float = 1.0,
        poll_ms: int = POLL_INTERVAL_MS,
        model: str = MODEL,
        ctx_candles: int = CTX_CANDLES,
        thinking_budget: int = THINKING_BUDGET,
        position_size_eth: float = POSITION_SIZE_ETH,
        slippage_bps: int = SLIPPAGE_BPS,
    ):
        self.initial_eth = initial_eth
        self.poll_ms = poll_ms
        self.model = model
        self.ctx_candles = ctx_candles
        self.thinking_budget = thinking_budget
        self.position_size_eth = position_size_eth
        self.slippage_bps = slippage_bps

        # Cost model from tweet
        self.cost_table = {
            "claude-opus-5": {"ctx24": 0.0040, "ctx48": 0.0183, "ctx72": 0.0444},
            "fable-5.1": {"ctx96": 0.1667},
        }

        self.trades: List[Trade] = []
        self.balance_eth = initial_eth
        self.holdings: Dict[str, float] = {}  # token -> amount

    def simulate_price(self, token: str, base_price: float, volatility: float = 0.02) -> float:
        """Simple random walk price simulation"""
        import random
        change = random.gauss(0, volatility)
        return max(0.000001, base_price * (1 + change))

    def decide(self, token: str, price: float, ctx: List[float]) -> Optional[str]:
        """Model decision stub — replace with real LLM call later"""
        # Simple momentum: if last 3 prices rising → buy
        if len(ctx) >= 3:
            if ctx[-1] > ctx[-2] > ctx[-3]:
                return "buy"
            if ctx[-1] < ctx[-2] < ctx[-3]:
                return "sell"
        return None

    def execute(self, token: str, side: str, price: float) -> Trade:
        """Execute simulated trade"""
        amount_eth = self.position_size_eth
        slippage = self.slippage_bps / 10000.0

        if side == "buy":
            effective_price = price * (1 + slippage)
            amount_token = amount_eth / effective_price
            fee = amount_eth * 0.003  # 0.3% fee
            self.balance_eth -= (amount_eth + fee)
            self.holdings[token] = self.holdings.get(token, 0) + amount_token
            pnl = 0.0
        else:  # sell
            effective_price = price * (1 - slippage)
            amount_token = self.holdings.get(token, 0)
            if amount_token <= 0:
                amount_token = amount_eth / effective_price
            received_eth = amount_token * effective_price
            fee = received_eth * 0.003
            self.balance_eth += (received_eth - fee)
            self.holdings[token] = 0
            pnl = received_eth - fee - amount_eth  # rough

        trade = Trade(
            timestamp=datetime.now(),
            token=token,
            side=side,
            price=price,
            amount_eth=amount_eth,
            amount_token=amount_token,
            slippage_bps=self.slippage_bps,
            fee_eth=fee,
            pnl_eth=pnl,
        )
        self.trades.append(trade)
        return trade

    def run(
        self,
        token: str = "TEST",
        base_price: float = 0.0001,
        days: int = 7,
        decisions_per_day: int = 24,
    ) -> BacktestResult:
        """Run backtest simulation"""
        start = datetime.now() - timedelta(days=days)
        end = datetime.now()

        prices = []
        for _ in track(range(days * decisions_per_day), description="Simulating..."):
            p = self.simulate_price(token, base_price)
            prices.append(p)

            decision = self.decide(token, p, prices[-self.ctx_candles:])
            if decision and self.balance_eth >= self.position_size_eth:
                self.execute(token, decision, p)

            time.sleep(0.001)  # fast sim

        # Close any open positions at last price
        if token in self.holdings and self.holdings[token] > 0:
            last_price = prices[-1] if prices else base_price
            self.execute(token, "sell", last_price)

        result = BacktestResult(
            start=start,
            end=end,
            trades=self.trades,
            initial_eth=self.initial_eth,
            final_eth=self.balance_eth,
            total_pnl_eth=self.balance_eth - self.initial_eth,
            total_trades=len(self.trades),
        )

        if self.trades:
            wins = sum(1 for t in self.trades if t.pnl_eth > 0)
            result.win_rate = wins / len(self.trades)
            result.avg_slippage_bps = sum(t.slippage_bps for t in self.trades) / len(self.trades)

        # Cost calc from tweet table
        ctx_key = f"ctx{self.ctx_candles}"
        if self.model in self.cost_table and ctx_key in self.cost_table[self.model]:
            result.cost_per_decision = self.cost_table[self.model][ctx_key]
            result.daily_burn = result.cost_per_decision * decisions_per_day

        return result

    def print_result(self, result: BacktestResult):
        """Pretty print backtest summary"""
        s = result.summary()

        table = Table(title=f"Backtest Result | {self.model} | ctx={self.ctx_candles}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        for k, v in s.items():
            table.add_row(k, str(v))

        console.print(table)

        # Config echo (tweet format)
        console.print("\n[bold]Config:[/bold]")
        console.print(f"pollIntervalMs   {self.poll_ms}")
        console.print(f"model            {self.model}")
        console.print(f"ctxCandles       {self.ctx_candles}")
        console.print(f"thinkingBudget   {self.thinking_budget}")
        console.print(f"positionSizeEth  {self.position_size_eth}")
        console.print(f"slippageBps      {self.slippage_bps}")
        console.print(f"costPerDecision  ${result.cost_per_decision:.4f}")
        console.print(f"dailyBurn        ${result.daily_burn:.2f}")


if __name__ == "__main__":
    engine = BacktestEngine(
        initial_eth=0.5,
        poll_ms=2420,
        model="claude-opus-5",
        ctx_candles=72,
        thinking_budget=1500,
        position_size_eth=0.0176,
        slippage_bps=106,
    )
    result = engine.run(days=3, decisions_per_day=12)
    engine.print_result(result)