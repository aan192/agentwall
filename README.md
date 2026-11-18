# AgentWall 🧱

**The daily roll-call wall for Agent ID holders.**

AgentWall is a small on-chain dApp on BNB Chain built for the Binance Wallet ×
BNB Chain **Agent ID Hackathon**. Every day, each holder of an Agent ID (a
`.ai` identity from the SPACE ID Agent ID registry) can check in exactly once,
build a consecutive-day streak, and leave a short "shout" on a public wall.

**Live dApp:** https://aan192.github.io/agentwall/
**Contract (BNB Chain mainnet):** [`0x3bffba48f59988b53d275cb49b03a7d4628a04b7`](https://bscscan.com/address/0x3bffba48f59988b53d275cb49b03a7d4628a04b7) — source verified on BscScan.

## How Agent ID is used (the core flow, not a decoration)

Agent ID is the product's only membership system — there is no sign-up, no
allowlist, and no account database:

- `checkIn()` calls `balanceOf(msg.sender)` on the official Agent ID registry
  (`0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F`) **inside the transaction**.
  If the caller holds no Agent ID, the transaction reverts with
  `"Agent ID required"`. Holding the identity *is* the ticket.
- Because the registry token is non-transferable and bound to the holder's
  wallet, every check-in, streak, and leaderboard position is provably tied to
  a real Agent ID — sybil accounts without an Agent ID simply cannot play.
- The frontend reads the same registry to show the connected wallet's Agent
  ID status, and resolves each participant's own public `.ai` name for
  display next to their own check-ins (best-effort, from the registry's own
  on-chain metadata).

## What the contract does

- One check-in per Agent ID address per UTC day.
- Tracks per-agent current streak (consecutive days), best streak, lifetime
  check-ins, and last check-in day, plus global counters (`totalCheckIns`,
  `uniqueAgents`).
- An optional shout of up to 140 bytes is carried in the `CheckIn` event —
  shouts are **emitted, never stored**, keeping check-ins cheap and state
  minimal. Frontends rebuild the wall feed and the streak leaderboard purely
  from event logs.

## Design guarantees

- **No owner, no admin functions.** Nobody — including the deployer — can
  pause, edit, or remove a check-in.
- **No funds.** Every function is non-payable; the contract can never
  receive, hold, or move BNB or tokens.
- **No approvals.** The dApp never asks users for token approvals; a check-in
  is a single plain transaction the user confirms in their own wallet.
- **No upgradeability / proxy.** The deployed bytecode is final.
- **No login sessions, no QR pairing, no credential collection.** The dApp
  uses a standard injected-wallet connection only.

## Repository layout

- `contracts/AgentWall.sol` — the wall contract (+ the registry interface).
- `contracts/MockAgentIdRegistry.sol` — mock registry used by the tests.
- `test/run_tests.py` — local test suite (eth-tester / py-evm): 24 checks
  covering the holder gate, once-per-day rule, 140-byte shout limit, streak
  increment/reset, live streak lapse, counters, and behavior when an Agent
  ID is revoked. Latest output: `test/test-results.txt`.
- `scripts/deploy.py` — the deployment script actually used (with its gas
  safety gates), kept for transparency.
- `index.html` — the single-page dApp served via GitHub Pages.
- `DEPLOYED.md` — deployment record (tx hash, gas cost, read-back checks).

## Build / test

```bash
# compile (solc 0.8.26, optimizer 200 runs)
solc --optimize --optimize-runs 200 --bin --abi \
  -o build --overwrite contracts/AgentWall.sol contracts/MockAgentIdRegistry.sol

# test (python venv with eth-tester, py-evm, eth-abi, eth-utils)
python test/run_tests.py
```

## License

MIT — see `LICENSE`.
