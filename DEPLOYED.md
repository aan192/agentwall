# AgentWall — Deployment Record

- **Network:** BNB Chain mainnet (chainId 56)
- **Contract address:** `0x3bffba48f59988b53d275cb49b03a7d4628a04b7`
- **BscScan:** https://bscscan.com/address/0x3bffba48f59988b53d275cb49b03a7d4628a04b7
- **Deploy transaction:** `0x0092aa0bee677a60fa618a5dea020bf842320b0e47ab5a56dccdc06b07c98310`
- **Block:** 134315716
- **Deployer:** `0xfb39efcA08Ec9c19667B729fdEBb4231a9DE5984` ("wallet Muse")
- **Gas used:** 479,778 @ 0.05 gwei = **0.00002399 BNB** actual cost
- **Constructor argument:** Agent ID registry `0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F`
- **Compiler:** solc 0.8.26+commit.8a97fa7a, optimizer enabled, 200 runs
- **Receipt status:** 1 (success)

## Post-deploy on-chain read-backs (verified)

- `totalCheckIns()` = 0
- `uniqueAgents()` = 0
- `agentIdRegistry()` = `0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F` ✓
- `hasAgentId(0xeCFE96Dc8127595edC0196949Ef1b9f901C75422)` = **true** (the builder's
  Agent ID wallet — the gate works live against the real registry)
- `hasAgentId(deployer)` = false (deployer holds no Agent ID, as expected)

## Source verification

- **Sourcify: EXACT MATCH** (creation + runtime), verified 2026-11-18
  13:05 UTC, matchId 59469254 —
  https://sourcify.dev/#/lookup/0x3bffba48f59988b53d275cb49b03a7d4628a04b7
- Sourcify automatically propagated the verification to the Etherscan-family
  backend (BscScan) in the same job (external verification id
  kves356gfpbuyskbrz9i2y1nvt6fxqpsf5fg8ff66mctfc88y9). The BscScan web page
  itself returns 403 to this server's fetches (bot protection), so the green
  "verified" display on bscscan.com could not be screenshot-confirmed from
  here — check the address page in a normal browser; if it does not show as
  verified, the fallback is a manual verify on BscScan (free account,
  user-side) with: solc 0.8.26, optimizer on, 200 runs, source
  `contracts/AgentWall.sol`, constructor arg = the registry address (ABI-encoded).

## Public surfaces

- Repo: https://github.com/aan192/agentwall
- Live dApp (GitHub Pages): https://aan192.github.io/agentwall/

## Tests

Local suite (eth-tester/py-evm vs a mock registry): **24/24 checks passed**
— see `test/test-results.txt`. Recompiled bytecode from source matches the
deployed artifact byte-for-byte.
