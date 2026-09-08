# Robinhood Chain Trading Terminal

Python CLI untuk price monitoring + wallet management di Robinhood Chain (chain ID 4663).

## Setup

```bash
cd /home/ubuntu/robinhood-terminal
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python3 terminal.py
```

Menu:
- `1` Wallet Info — lihat address, balance, explorer link
- `2` Create New Wallet — generate wallet baru (simpan ke `~/.robinhood/wallet.json`)
- `3` Export Private Key — **DANGER** (tampilkan private key)
- `4` Monitor Balances — cek balance ETH + token
- `5` Live Monitor — auto-refresh setiap 3 detik (Ctrl+C stop)
- `6` Backtest (simulated) — full params dari tweet
- `7` GMGN Search — token discovery + risk
- `8` Bridge ETH — Arbitrum → Robinhood (Relay/Across/LiFi)
- `9` Swap (Uniswap V3) — stub execution (verify router!)
- `0` Exit

## Wallet

Wallet disimpan di `~/.robinhood/wallet.json`:
```json
{
  "address": "0x...",
  "private_key": "0x...",
  "chain_id": 4663
}
```

Atau set env var:
```bash
export ROBINHOOD_PK="0x_your_private_key"
```

## Network

- Chain ID: 4663
- RPC: https://rpc.mainnet.chain.robinhood.com
- Explorer: https://robinhoodchain.blockscout.com

## Token Addresses (verify dulu!)

Lihat di Blockscout sebelum trading. Contoh:
- PONS: `0x39dbed3a2bd333467115de45665cc57f813c4571`

## Config

Edit `config.py`:
- `POLL_INTERVAL_MS` — polling interval
- `POSITION_SIZE_ETH` — default size
- `SLIPPAGE_BPS` — slippage tolerance

## Safety

- Private key **hanya** di file lokal
- Jangan commit `wallet.json` atau `.env`
- Verify contract addresses di explorer sebelum approve/spend
- Robinhood Chain masih baru — high risk

## Done (semua implemented)

- ✅ Trading execution (Uniswap V3 exactInputSingle in trade.py)
- ✅ GMGN integration (search, token info, risk in gmgn.py)
- ✅ Bridge ETH (Arbitrum → Robinhood options in bridge.py)
- ✅ Backtesting engine (full tweet params in backtest.py)
- ✅ Telegram alerts (price/trade/backtest in alerts.py)
- ✅ GitHub + Vercel ready (vercel.json, deploy.sh)

## References

- Skill: `robinhood-chain` (`.hermes/skills/robinhood-chain/SKILL.md`)
- Tweet: https://x.com/w1nklerr/status/2096964317107077567