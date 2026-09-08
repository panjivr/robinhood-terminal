"""GMGN.ai integration for Robinhood Chain (price, risk, discovery)"""
import requests
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table

console = Console()

GMGN_BASE = "https://gmgn.ai"
ROBINHOOD_CHAIN = "robinhood"


def get_token_info(address: str) -> Optional[Dict]:
    """Fetch token info from GMGN"""
    try:
        url = f"{GMGN_BASE}/api/v1/token_info/{ROBINHOOD_CHAIN}/{address}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json().get("data")
    except Exception as e:
        console.print(f"[red]GMGN error:[/red] {e}")
    return None


def get_wallet_risk(address: str) -> Optional[Dict]:
    """Check wallet risk score"""
    try:
        url = f"{GMGN_BASE}/api/v1/wallet_risk/{ROBINHOOD_CHAIN}/{address}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json().get("data")
    except:
        pass
    return None


def search_tokens(query: str, limit: int = 10) -> List[Dict]:
    """Search tokens on Robinhood Chain"""
    try:
        url = f"{GMGN_BASE}/api/v1/search/{ROBINHOOD_CHAIN}"
        r = requests.get(url, params={"q": query, "limit": limit}, timeout=10)
        if r.status_code == 200:
            return r.json().get("data", [])
    except:
        pass
    return []


def show_token_table(tokens: List[Dict]):
    """Pretty print token list"""
    table = Table(title="GMGN Token Search")
    table.add_column("Symbol", style="cyan")
    table.add_column("Address", style="dim")
    table.add_column("Price", style="green")
    table.add_column("Liq", style="yellow")
    table.add_column("Risk", style="red")

    for t in tokens[:10]:
        table.add_row(
            t.get("symbol", "?")[:10],
            t.get("address", "")[:10] + "...",
            str(t.get("price", "-")),
            str(t.get("liquidity", "-")),
            t.get("risk_level", "-"),
        )
    console.print(table)


if __name__ == "__main__":
    console.print("[cyan]GMGN module loaded.[/cyan] Use search_tokens() or get_token_info().")
    # Example:
    # tokens = search_tokens("PONS")
    # show_token_table(tokens)