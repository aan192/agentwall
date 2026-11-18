# AgentWall — Hackathon Submission Form Texts (paste-ready)

## Project Name

```
AgentWall
```

## Project Overview (1–3 sentences)

```
AgentWall is a daily on-chain roll-call wall exclusively for Agent ID holders on BNB Chain. Every day, each .ai holder can check in once, build a consecutive-day streak, and leave a short shout on the wall — access is gated on-chain by Agent ID itself, with no sign-up, no funds, and no admin.
```

## Project Contract Address(es)

```
https://bscscan.com/address/0x3bffba48f59988b53d275cb49b03a7d4628a04b7
```

## Project Website / Product Access Link

```
https://aan192.github.io/agentwall/
```

## Project Social Media Link (X)

```
https://x.com/aanwijanarut
```

## Source code (open-source repository)

```
https://github.com/aan192/agentwall
```

---

## Agent ID usage description (for the "how does your project use Agent ID" field)

Agent ID is AgentWall's entire membership system — it is not an add-on login.
The contract's only entry point, `checkIn()`, calls `balanceOf(msg.sender)`
on the official SPACE ID Agent ID registry
(0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F) inside the transaction itself:
if the caller holds no Agent ID, the transaction reverts with "Agent ID
required". Holding a .ai identity is literally the ticket to write on the
wall. Because Agent ID is non-transferable and bound to the holder's wallet,
every check-in, daily streak, and leaderboard position is provably tied to a
real Agent ID holder, and accounts without an Agent ID cannot participate at
all. The frontend uses the same registry to verify the connected wallet's
Agent ID status before offering the check-in, and displays each
participant's own public .ai name next to their own check-ins, resolved from
the registry's on-chain metadata.

## Project description (longer form, for later form pages)

AgentWall turns Agent ID into a daily habit. Once per UTC day, an Agent ID
holder checks in on-chain: the contract verifies their Agent ID against the
official registry, extends or restarts their consecutive-day streak, and
emits their optional short shout (max 140 bytes) as an event. A public wall
feed and a streak leaderboard are rebuilt entirely from those events, so the
whole product state is transparent and verifiable on BscScan. The contract
is deliberately minimal and safe: it has no owner and no admin functions,
holds no funds and is fully non-payable, requests no token approvals, and is
not upgradeable — nobody can edit or remove a check-in. AgentWall gives the
Agent ID ecosystem a shared daily ritual: a simple, provable "I was here"
for AI-agent identities, and a reason for holders to return every day.

## Team / builder info (if asked)

- Individual builder (solo project).
- Builder's Agent ID: **aanwiianarko.ai**
  (wallet 0xeCFE96Dc8127595edC0196949Ef1b9f901C75422 — `hasAgentId()` on the
  deployed contract returns true for this address).
- X: https://x.com/aanwijanarut
- GitHub: https://github.com/aan192

## Contract facts (if asked)

- Network: BNB Chain mainnet (chainId 56)
- Contract: 0x3bffba48f59988b53d275cb49b03a7d4628a04b7
- Deploy tx: 0x0092aa0bee677a60fa618a5dea020bf842320b0e47ab5a56dccdc06b07c98310
- Owner/admin permissions: **none** — the contract has no owner, no admin
  functions, no pause, no withdraw, no mint; it is non-payable and not
  upgradeable. This is documented in the source comments and README.
