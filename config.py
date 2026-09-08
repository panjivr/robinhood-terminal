"""Robinhood Chain Trading Terminal - Config"""
import os
from pathlib import Path

# Network
CHAIN_ID = 4663
RPC_URL = "https://rpc.mainnet.chain.robinhood.com"
EXPLORER = "https://robinhoodchain.blockscout.com"

# Wallet - loaded from env or file
WALLET_PRIVATE_KEY = os.getenv("ROBINHOOD_PK", "")
WALLET_PATH = Path.home() / ".robinhood" / "wallet.json"

# Price monitoring
POLL_INTERVAL_MS = 2420
CTX_CANDLES = 72

# Trading params (from tweet example)
POSITION_SIZE_ETH = 0.0176
SLIPPAGE_BPS = 106  # 1.06%

# Model config (for reference, not used in monitoring)
MODEL = "claude-opus-5"
THINKING_BUDGET = 1500

# Token addresses (verify on explorer before trading)
KNOWN_TOKENS = {
    "ETH": "0x0000000000000000000000000000000000000000",
    "WETH": "0x4200000000000000000000000000000000000006",  # typical L2
    "PONS": "0x39dbed3a2bd333467115de45665cc57f813c4571",
}