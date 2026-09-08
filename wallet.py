"""Wallet management for Robinhood Chain"""
import json
from pathlib import Path
from eth_account import Account
from web3 import Web3
from rich.console import Console
from rich.table import Table
from config import RPC_URL, CHAIN_ID, WALLET_PATH, EXPLORER

console = Console()
w3 = Web3(Web3.HTTPProvider(RPC_URL))


def create_wallet():
    """Generate new wallet"""
    acct = Account.create()
    wallet_data = {
        "address": acct.address,
        "private_key": acct.key.hex(),
        "chain_id": CHAIN_ID,
    }

    WALLET_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(WALLET_PATH, "w") as f:
        json.dump(wallet_data, f, indent=2)

    console.print(f"[green]Wallet created:[/green] {acct.address}")
    console.print(f"[yellow]Saved to:[/yellow] {WALLET_PATH}")
    console.print(f"[red]Private key:[/red] {acct.key.hex()[:16]}... (keep safe!)")
    return wallet_data


def load_wallet():
    """Load wallet from file or create if missing"""
    if WALLET_PATH.exists():
        with open(WALLET_PATH) as f:
            data = json.load(f)
        console.print(f"[cyan]Loaded wallet:[/cyan] {data['address']}")
        return data

    console.print("[yellow]No wallet found. Creating new...[/yellow]")
    return create_wallet()


def get_balance(address):
    """Get ETH balance"""
    balance_wei = w3.eth.get_balance(Web3.to_checksum_address(address))
    balance_eth = w3.from_wei(balance_wei, "ether")
    return float(balance_eth)


def show_wallet_info():
    """Display wallet status"""
    wallet = load_wallet()
    addr = wallet["address"]
    balance = get_balance(addr)

    table = Table(title="Robinhood Chain Wallet")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Address", addr)
    table.add_row("Balance", f"{balance:.6f} ETH")
    table.add_row("Chain ID", str(CHAIN_ID))
    table.add_row("Explorer", f"{EXPLORER}/address/{addr}")

    console.print(table)
    return wallet


def export_wallet():
    """Show full private key (user must confirm)"""
    wallet = load_wallet()
    console.print("[red bold]WARNING: Never share this key![/red bold]")
    console.print(f"Private Key: {wallet['private_key']}")
    return wallet["private_key"]


if __name__ == "__main__":
    show_wallet_info()