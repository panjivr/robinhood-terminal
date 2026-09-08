"""Bridge ETH from Arbitrum to Robinhood Chain.

Primary: portal.arbitrum.io/bridge (canonical, 7-day challenge on withdraw)
Fast: Relay, Across, LiFi (minutes, higher fee)
"""
from rich.console import Console

console = Console()

ARBITRUM_CHAIN_ID = 42161
ROBINHOOD_CHAIN_ID = 4663

BRIDGES = {
    "canonical": {
        "name": "Arbitrum Bridge",
        "url": "https://portal.arbitrum.io/bridge",
        "time_deposit": "10-30 min",
        "time_withdraw": "7 days (challenge)",
        "fee": "gas only",
    },
    "relay": {
        "name": "Relay",
        "url": "https://relay.link",
        "time": "1-5 min",
        "fee": "~0.1-0.5%",
    },
    "across": {
        "name": "Across",
        "url": "https://across.to",
        "time": "1-3 min",
        "fee": "dynamic",
    },
    "lifi": {
        "name": "LiFi",
        "url": "https://li.fi",
        "time": "2-10 min",
        "fee": "aggregator",
    },
}


def show_bridge_options():
    """Display bridge options"""
    console.print("\n[bold cyan]Bridge ETH: Arbitrum → Robinhood Chain[/bold cyan]")
    console.print(f"From: Chain {ARBITRUM_CHAIN_ID} | To: Chain {ROBINHOOD_CHAIN_ID}\n")

    for key, b in BRIDGES.items():
        console.print(f"[green]{key}[/green]: {b['name']}")
        console.print(f"  URL: {b['url']}")
        if "time_deposit" in b:
            console.print(f"  Deposit: {b['time_deposit']} | Withdraw: {b['time_withdraw']}")
        else:
            console.print(f"  Time: {b['time']} | Fee: {b['fee']}")
        console.print()


def bridge_instructions(amount_eth: float, bridge: str = "relay"):
    """Print step-by-step bridge instructions"""
    b = BRIDGES.get(bridge, BRIDGES["relay"])
    console.print(f"\n[yellow]Bridge {amount_eth} ETH via {b['name']}[/yellow]")
    console.print(f"1. Go to {b['url']}")
    console.print("2. Connect wallet (Arbitrum network)")
    console.print(f"3. Select destination: Robinhood Chain (ID {ROBINHOOD_CHAIN_ID})")
    console.print(f"4. Enter amount: {amount_eth} ETH")
    console.print("5. Approve + confirm transaction")
    console.print(f"6. Wait ~{b.get('time', b.get('time_deposit', '5 min'))}")
    console.print("\n[red]WARNING: Withdrawals to Arbitrum have 7-day challenge period on canonical bridge.[/red]")


if __name__ == "__main__":
    show_bridge_options()
    bridge_instructions(0.1, "relay")