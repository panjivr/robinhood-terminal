"""Telegram alerts for trading terminal (price, trade, backtest result)"""
import os
from typing import Optional
from rich.console import Console

console = Console()

# Load from env or skill config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send_alert(message: str, chat_id: Optional[str] = None) -> bool:
    """Send message via Telegram Bot API"""
    if not TELEGRAM_BOT_TOKEN:
        console.print("[yellow]No TELEGRAM_BOT_TOKEN set. Alert skipped.[/yellow]")
        return False

    import requests

    cid = chat_id or TELEGRAM_CHAT_ID or "me"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": cid, "text": message, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        console.print(f"[red]Telegram error:[/red] {e}")
        return False


def alert_trade(token: str, side: str, amount: float, price: float, pnl: float = 0):
    """Trade execution alert"""
    msg = f"🦍 <b>Robinhood Trade</b>\n{side.upper()} {amount:.4f} {token} @ ${price:.6f}"
    if pnl:
        msg += f"\nPnL: {pnl:+.4f} ETH"
    send_alert(msg)


def alert_backtest(result: dict):
    """Backtest summary alert"""
    msg = (
        f"📊 <b>Backtest Done</b>\n"
        f"PnL: {result.get('pnl_eth', 0):+.4f} ETH ({result.get('pnl_pct', 0):+.1f}%)\n"
        f"Win: {result.get('win_rate', 0):.0f}% | Trades: {result.get('trades', 0)}\n"
        f"Burn: ${result.get('daily_burn_usd', 0):.2f}/day"
    )
    send_alert(msg)


def alert_price(token: str, price: float, change_24h: float):
    """Price movement alert"""
    emoji = "📈" if change_24h > 0 else "📉"
    msg = f"{emoji} <b>{token}</b> ${price:.6f} ({change_24h:+.1f}%)"
    send_alert(msg)


if __name__ == "__main__":
    console.print("[cyan]Alerts module loaded.[/cyan] Set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID to enable.")
    # send_alert("Robinhood Terminal ready ✅")