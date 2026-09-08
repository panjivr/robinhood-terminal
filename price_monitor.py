"""Price monitoring for Robinhood Chain tokens"""
import time
import requests
from rich.console import Console
from rich.table import Table
from rich.live import Live
from web3 import Web3
from config import RPC_URL, CHAIN_ID, POLL_INTERVAL_MS, KNOWN_TOKENS

console = Console()
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Uniswap V3 Quoter ABI (minimal)
QUOTER_ABI = [
    {
        "inputs": [
            {"name": "tokenIn", "type": "address"},
            {"name": "tokenOut", "type": "address"},
            {"name": "fee", "type": "uint24"},
            {"name": "amountIn", "type": "uint256"},
            {"name": "sqrtPriceLimitX96", "type": "uint160"},
        ],
        "name": "quoteExactInputSingle",
        "outputs": [{"name": "amountOut", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
]

# Quoter address on Robinhood Chain (verify!)
QUOTER = "0xb27308f9F3D72fE6F8A2d8f4a8c8C6C8C6C8C6C8"  # placeholder


def get_eth_price_usd():
    """Get ETH price from CoinGecko"""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "ethereum", "vs_currencies": "usd"},
            timeout=5,
        )
        return r.json()["ethereum"]["usd"]
    except:
        return None


def get_token_balance(token_address, wallet_address):
    """Get ERC20 balance"""
    if token_address == KNOWN_TOKENS["ETH"]:
        return w3.eth.get_balance(Web3.to_checksum_address(wallet_address))

    erc20_abi = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function",
        },
    ]

    try:
        token = w3.eth.contract(
            address=Web3.to_checksum_address(token_address), abi=erc20_abi
        )
        balance = token.functions.balanceOf(
            Web3.to_checksum_address(wallet_address)
        ).call()
        decimals = token.functions.decimals().call()
        symbol = token.functions.symbol().call()
        return {"balance": balance, "decimals": decimals, "symbol": symbol}
    except Exception as e:
        return {"error": str(e)}


def monitor_wallet(wallet_address, tokens=None):
    """Live monitor wallet balances"""
    if tokens is None:
        tokens = list(KNOWN_TOKENS.values())

    eth_price = get_eth_price_usd()

    table = Table(title=f"Wallet Monitor | {wallet_address[:10]}...")
    table.add_column("Token", style="cyan")
    table.add_column("Balance", style="green")
    table.add_column("Value (USD)", style="yellow")

    for token_addr in tokens:
        bal = get_token_balance(token_addr, wallet_address)
        if isinstance(bal, dict) and "error" not in bal:
            human = bal["balance"] / (10 ** bal["decimals"])
            val = human * (eth_price or 0) if token_addr == KNOWN_TOKENS["ETH"] else 0
            table.add_row(
                bal["symbol"], f"{human:.6f}", f"${val:.2f}" if val else "-"
            )
        elif isinstance(bal, int):
            # ETH
            eth = w3.from_wei(bal, "ether")
            val = float(eth) * (eth_price or 0)
            table.add_row("ETH", f"{eth:.6f}", f"${val:.2f}")

    console.print(table)
    console.print(f"[dim]ETH Price: ${eth_price or 'N/A'}[/dim]")
    console.print(f"[dim]Poll: {POLL_INTERVAL_MS}ms | Chain: {CHAIN_ID}[/dim]")


def live_monitor(wallet_address, refresh_sec=3):
    """Continuous live monitor"""
    with Live(refresh_per_second=1, console=console) as live:
        while True:
            table = Table(title="Live Monitor (Ctrl+C to stop)")
            table.add_column("Token", style="cyan")
            table.add_column("Balance", style="green")

            eth_bal = get_token_balance(KNOWN_TOKENS["ETH"], wallet_address)
            eth = w3.from_wei(eth_bal, "ether")
            table.add_row("ETH", f"{eth:.6f}")

            for name, addr in KNOWN_TOKENS.items():
                if name == "ETH":
                    continue
                bal = get_token_balance(addr, wallet_address)
                if isinstance(bal, dict) and "symbol" in bal:
                    human = bal["balance"] / (10 ** bal["decimals"])
                    table.add_row(bal["symbol"], f"{human:.6f}")

            live.update(table)
            time.sleep(refresh_sec)


if __name__ == "__main__":
    from wallet import load_wallet

    wallet = load_wallet()
    monitor_wallet(wallet["address"])