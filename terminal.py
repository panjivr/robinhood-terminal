"""Main trading terminal CLI for Robinhood Chain"""
import json
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from config import (
    CHAIN_ID, RPC_URL, EXPLORER,
    POLL_INTERVAL_MS, MODEL, CTX_CANDLES, THINKING_BUDGET,
    POSITION_SIZE_ETH, SLIPPAGE_BPS
)
from wallet import show_wallet_info, create_wallet, export_wallet, load_wallet
from price_monitor import monitor_wallet, live_monitor
from backtest import BacktestEngine, BacktestResult

console = Console()


def show_banner():
    banner = """
[bold cyan]ROBINHOOD CHAIN TRADING TERMINAL[/bold cyan]
Chain ID: 4663 | RPC: rpc.mainnet.chain.robinhood.com
    """
    console.print(Panel(banner.strip(), border_style="cyan"))


def main_menu():
    show_banner()

    while True:
        console.print("\n[bold]Menu:[/bold]")
        console.print("  [cyan]1[/cyan] Wallet Info")
        console.print("  [cyan]2[/cyan] Create New Wallet")
        console.print("  [cyan]3[/cyan] Export Private Key (DANGER)")
        console.print("  [cyan]4[/cyan] Monitor Balances")
        console.print("  [cyan]5[/cyan] Live Monitor (auto-refresh)")
        console.print("  [cyan]6[/cyan] Backtest (simulated)")
        console.print("  [cyan]7[/cyan] Live Trade (stub)")
        console.print("  [cyan]0[/cyan] Exit")

        choice = Prompt.ask("\nSelect", choices=["0", "1", "2", "3", "4", "5", "6", "7"], default="1")

        if choice == "0":
            console.print("[yellow]Goodbye![/yellow]")
            sys.exit(0)

        elif choice == "1":
            show_wallet_info()

        elif choice == "2":
            if Confirm.ask("Create new wallet? (old one will be overwritten)"):
                create_wallet()

        elif choice == "3":
            if Confirm.ask("[red]Show private key?[/red]"):
                export_wallet()

        elif choice == "4":
            wallet = load_wallet()
            monitor_wallet(wallet["address"])

        elif choice == "5":
            wallet = load_wallet()
            try:
                live_monitor(wallet["address"])
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopped.[/yellow]")

        elif choice == "6":
            run_backtest_menu()

        elif choice == "7":
            run_live_trade_stub()


def run_backtest_menu():
    console.print("\n[bold cyan]Backtest Engine[/bold cyan]")
    console.print("Matches tweet config: pollIntervalMs, model, ctxCandles, thinkingBudget, positionSizeEth, slippageBps")

    initial = float(Prompt.ask("Initial ETH", default="0.5"))
    days = int(Prompt.ask("Days to simulate", default="7"))
    decisions = int(Prompt.ask("Decisions per day", default="24"))

    engine = BacktestEngine(
        initial_eth=initial,
        poll_ms=POLL_INTERVAL_MS,
        model=MODEL,
        ctx_candles=CTX_CANDLES,
        thinking_budget=THINKING_BUDGET,
        position_size_eth=POSITION_SIZE_ETH,
        slippage_bps=SLIPPAGE_BPS,
    )
    result = engine.run(days=days, decisions_per_day=decisions)
    engine.print_result(result)

    # Save result
    out = Path.home() / ".robinhood" / "backtest_results.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "config": {
                "pollIntervalMs": POLL_INTERVAL_MS,
                "model": MODEL,
                "ctxCandles": CTX_CANDLES,
                "thinkingBudget": THINKING_BUDGET,
                "positionSizeEth": POSITION_SIZE_ETH,
                "slippageBps": SLIPPAGE_BPS,
            },
            "result": result.summary(),
        }) + "\n")
    console.print(f"[dim]Saved to {out}[/dim]")


def run_live_trade_stub():
    console.print("\n[bold red]LIVE TRADE STUB[/bold red]")
    console.print("This is a placeholder. Real execution requires:")
    console.print("  - Verified token contract addresses")
    console.print("  - Uniswap V3/V4 router on Robinhood Chain")
    console.print("  - approve() + exactInputSingle() calls")
    console.print("  - Slippage protection + gas estimation")
    console.print("\n[yellow]Not implemented yet to avoid accidental spends.[/yellow]")

    if Confirm.ask("Show example swap code?"):
        console.print("""
from web3 import Web3
# Example (DO NOT RUN without verification):
# router = w3.eth.contract(address=ROUTER, abi=UNISWAP_V3_ROUTER_ABI)
# tx = router.functions.exactInputSingle({...}).build_transaction({...})
# signed = w3.eth.account.sign_transaction(tx, private_key)
# w3.eth.send_raw_transaction(signed.rawTransaction)
        """)


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n[yellow]Exit.[/yellow]")
        sys.exit(0)