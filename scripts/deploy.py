#!/usr/bin/env python3
"""Deploy AgentWall to BNB Chain mainnet.

Deployer: "wallet Muse" 0xfb39efcA08Ec9c19667B729fdEBb4231a9DE5984
(key read locally from ~/workspace/agent-wallet/key-evm.txt — never printed).

Safety gates (all enforced BEFORE any broadcast):
  - derived address must equal the expected deployer address
  - eth_estimateGas must succeed for the exact initcode + constructor arg
  - estimated cost (estimate x live gasPrice) must be <= 0.0003 BNB
  - deployer balance must cover the gas limit (estimate + 20%) x gasPrice

Usage:
  ~/workspace/synmerco/venv/bin/python scripts/deploy.py            # dry run: estimate + plan only
  ~/workspace/synmerco/venv/bin/python scripts/deploy.py --broadcast
"""
import json
import sys
import time

import requests
from eth_account import Account
from eth_abi import encode as abi_encode

RPC = "https://bsc-dataseed.binance.org"
CHAIN_ID = 56
REGISTRY = "0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F"  # SPACE ID Agent ID
EXPECTED_DEPLOYER = "0xfb39efcA08Ec9c19667B729fdEBb4231a9DE5984"
KEY_FILE = "/home/hatch/workspace/agent-wallet/key-evm.txt"
ARTIFACT = "/home/hatch/workspace/agentwall/build/AgentWall.json"
OUT_FILE = "/home/hatch/workspace/agentwall/build/deployment.json"
MAX_COST_BNB = 0.0003


def rpc(method, params):
    r = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                      timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    j = r.json()
    if "error" in j:
        raise RuntimeError(f"{method}: {j['error']}")
    return j["result"]


def main():
    broadcast = "--broadcast" in sys.argv

    key = open(KEY_FILE).read().strip()
    acct = Account.from_key(key)
    assert acct.address.lower() == EXPECTED_DEPLOYER.lower(), \
        f"key/address mismatch: {acct.address} != {EXPECTED_DEPLOYER}"
    print(f"deployer         : {acct.address} (key verified, not printed)")

    art = json.load(open(ARTIFACT))
    init = art["bytecode"] + abi_encode(["address"], [REGISTRY]).hex()

    balance = int(rpc("eth_getBalance", [acct.address, "latest"]), 16)
    gas_price = int(rpc("eth_gasPrice", []), 16)
    estimate = int(rpc("eth_estimateGas", [{"from": acct.address, "data": init}]), 16)
    gas_limit = int(estimate * 1.2)
    est_cost = estimate * gas_price
    limit_cost = gas_limit * gas_price

    print(f"registry (ctor)  : {REGISTRY}")
    print(f"balance          : {balance / 1e18:.8f} BNB")
    print(f"gas price        : {gas_price / 1e9:.3f} gwei")
    print(f"estimated gas    : {estimate:,}  (limit with +20%: {gas_limit:,})")
    print(f"estimated cost   : {est_cost / 1e18:.8f} BNB  (gate: <= {MAX_COST_BNB} BNB)")

    if est_cost > int(MAX_COST_BNB * 1e18):
        print("REFUSED: estimated cost exceeds the 0.0003 BNB gate. Nothing broadcast.")
        return 1
    if balance < limit_cost:
        print("REFUSED: balance does not cover the buffered gas cost. Nothing broadcast.")
        return 1

    if not broadcast:
        print("\nDRY RUN only — no transaction sent. Re-run with --broadcast to deploy.")
        return 0

    nonce = int(rpc("eth_getTransactionCount", [acct.address, "pending"]), 16)
    tx = {
        "chainId": CHAIN_ID,
        "nonce": nonce,
        "gasPrice": gas_price,
        "gas": gas_limit,
        "value": 0,
        "data": bytes.fromhex(init[2:] if init.startswith("0x") else init),
    }
    signed = acct.sign_transaction(tx)
    tx_hash = rpc("eth_sendRawTransaction", ["0x" + signed.raw_transaction.hex()])
    print(f"\nbroadcast        : {tx_hash}")

    receipt = None
    for _ in range(60):
        try:
            receipt = rpc("eth_getTransactionReceipt", [tx_hash])
        except RuntimeError:
            receipt = None
        if receipt:
            break
        time.sleep(3)
    if not receipt:
        print("Receipt not seen yet — check the tx hash on BscScan before doing anything else.")
        return 2
    if receipt["status"] != "0x1":
        print(f"DEPLOY FAILED on-chain (status 0). Tx: {tx_hash}")
        return 3

    contract = receipt["contractAddress"]
    print(f"contract address : {contract}")
    print(f"block            : {int(receipt['blockNumber'], 16)}")
    print(f"gas used         : {int(receipt['gasUsed'], 16):,} "
          f"({int(receipt['gasUsed'], 16) * gas_price / 1e18:.8f} BNB)")
    print(f"BscScan          : https://bscscan.com/address/{contract}")
    json.dump({
        "contract": contract,
        "txHash": tx_hash,
        "block": int(receipt["blockNumber"], 16),
        "deployer": acct.address,
        "registry": REGISTRY,
        "chainId": CHAIN_ID,
    }, open(OUT_FILE, "w"), indent=2)
    print(f"saved            : {OUT_FILE}")
    print("\nNEXT: verify the source on BscScan (contract was compiled with "
          "solc 0.8.26, optimizer enabled, 200 runs) and fill the address "
          "into index.html + SUBMISSION.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
