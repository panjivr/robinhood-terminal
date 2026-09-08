"""Trading execution for Robinhood Chain (Uniswap V3/V4)"""
import os
from dataclasses import dataclass
from typing import Optional
from web3 import Web3
from eth_account import Account
from rich.console import Console
from config import RPC_URL, CHAIN_ID, WALLET_PATH, SLIPPAGE_BPS

console = Console()
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Uniswap V3 Router (verify on Blockscout for Robinhood Chain)
# Common L2 pattern: 0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45 (SwapRouter02)
UNISWAP_ROUTER = "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
UNISWAP_ROUTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "recipient", "type": "address"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMinimum", "type": "uint256"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
                "name": "params",
                "type": "tuple",
            }
        ],
        "name": "exactInputSingle",
        "outputs": [{"name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function",
    }
]

ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
]


@dataclass
class SwapResult:
    tx_hash: str
    amount_out: int
    gas_used: int
    effective_price: float


def load_private_key() -> Optional[str]:
    if os.getenv("ROBINHOOD_PK"):
        return os.getenv("ROBINHOOD_PK")
    if WALLET_PATH.exists():
        import json

        with open(WALLET_PATH) as f:
            return json.load(f)["private_key"]
    return None


def approve_token(token: str, spender: str, amount: int, pk: str) -> str:
    """Approve ERC20 spend"""
    acct = Account.from_key(pk)
    contract = w3.eth.contract(address=Web3.to_checksum_address(token), abi=ERC20_ABI)

    tx = contract.functions.approve(spender, amount).build_transaction(
        {
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "gas": 100000,
            "gasPrice": w3.eth.gas_price,
            "chainId": CHAIN_ID,
        }
    )
    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()


def swap_exact_input_single(
    token_in: str,
    token_out: str,
    amount_in: int,
    fee: int = 3000,  # 0.3%
    min_out: Optional[int] = None,
    pk: Optional[str] = None,
) -> SwapResult:
    """Execute Uniswap V3 exactInputSingle swap"""
    if pk is None:
        pk = load_private_key()
    if not pk:
        raise ValueError("No private key found. Set ROBINHOOD_PK or create wallet.")

    acct = Account.from_key(pk)
    router = w3.eth.contract(
        address=Web3.to_checksum_address(UNISWAP_ROUTER), abi=UNISWAP_ROUTER_ABI
    )

    # Calculate min_out with slippage
    if min_out is None:
        # Assume 1:1 for placeholder; real impl needs price oracle
        min_out = int(amount_in * (1 - SLIPPAGE_BPS / 10000))

    params = {
        "tokenIn": Web3.to_checksum_address(token_in),
        "tokenOut": Web3.to_checksum_address(token_out),
        "fee": fee,
        "recipient": acct.address,
        "amountIn": amount_in,
        "amountOutMinimum": min_out,
        "sqrtPriceLimitX96": 0,
    }

    tx = router.functions.exactInputSingle(params).build_transaction(
        {
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "gas": 300000,
            "gasPrice": w3.eth.gas_price,
            "chainId": CHAIN_ID,
            "value": 0,
        }
    )

    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    # Parse amountOut from logs (simplified)
    amount_out = 0
    for log in receipt.logs:
        if log.topics and log.topics[0].hex() == "0xc42079f...":  # Swap event
            pass  # real parse needed

    return SwapResult(
        tx_hash=tx_hash.hex(),
        amount_out=amount_out,
        gas_used=receipt.gasUsed,
        effective_price=0.0,
    )


def swap_eth_for_token(token_out: str, amount_eth: float, fee: int = 3000) -> str:
    """Convenience: ETH → Token (wraps WETH internally via router)"""
    pk = load_private_key()
    if not pk:
        raise ValueError("No PK")

    amount_wei = w3.to_wei(amount_eth, "ether")
    # For real impl: use multicall or SwapRouter02 native ETH support
    # Placeholder: direct WETH swap
    weth = "0x4200000000000000000000000000000000000006"  # L2 WETH
    return swap_exact_input_single(weth, token_out, amount_wei, fee, pk=pk).tx_hash


if __name__ == "__main__":
    console.print("[yellow]Trading module loaded. Use via terminal.py menu 7 or import.[/yellow]")
    console.print(f"Router: {UNISWAP_ROUTER}")
    console.print("WARNING: Verify router address on Blockscout before real use.")