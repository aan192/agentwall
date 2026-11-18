#!/usr/bin/env python3
"""AgentWall local test harness (eth-tester / py-evm).

Deploys MockAgentIdRegistry + AgentWall on a local in-memory chain and
proves the core behavior:
  1. non-holder check-in reverts ("Agent ID required")
  2. holder check-in works; event + stats + global counters correct
  3. second check-in on the same UTC day reverts
  4. shout > 140 bytes reverts; exactly 140 bytes is accepted
  5. streak increments on consecutive days
  6. streak resets to 1 after a gap day; best streak is kept
  7. streakOf reads 0 live once the chain is broken (before next check-in)
  8. a second holder is independent; uniqueAgents counts both
  9. revoking the mock Agent ID makes check-in revert again

Run:  /tmp/awtest-venv/bin/python test/run_tests.py
"""
import json
import sys
import time

from eth_tester import EthereumTester, PyEVMBackend
from eth_tester.exceptions import TransactionFailed
from eth_abi import encode as abi_encode, decode as abi_decode
from eth_utils import keccak

ROOT = __file__.rsplit("/test/", 1)[0]
DAY = 86400

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")


def sel(sig):
    return keccak(text=sig)[:4]


def call(t, to, sig, types, args, out_types):
    data = sel(sig) + (abi_encode(types, args) if types else b"")
    raw = t.call({"from": t.get_accounts()[0], "to": to, "data": "0x" + data.hex()})
    raw = bytes.fromhex(raw[2:] if isinstance(raw, str) else raw.hex())
    return abi_decode(out_types, raw)


def main():
    wall_art = json.load(open(f"{ROOT}/build/AgentWall.json"))
    mock_art = json.load(open(f"{ROOT}/build/MockAgentIdRegistry.json"))

    t = EthereumTester(PyEVMBackend())
    deployer, alice, bob, mallory = t.get_accounts()[:4]

    def send(frm, to, sig, types, args, value=0):
        tx = {"from": frm, "gas": 3_000_000, "value": value}
        if to is None:
            tx["data"] = args  # raw initcode for deploys
        else:
            data = sel(sig) + (abi_encode(types, args) if types else b"")
            tx["to"] = to
            tx["data"] = "0x" + data.hex()
        h = t.send_transaction(tx)
        return t.get_transaction_receipt(h)

    def deploy(frm, bytecode, types=None, args=None):
        init = bytes.fromhex(bytecode[2:])
        if types:
            init += abi_encode(types, args)
        r = send(frm, None, None, None, "0x" + init.hex())
        assert r["status"] == 1, "deploy failed"
        return r["contract_address"]

    # ---- deploy mock registry + wall -------------------------------------
    mock = deploy(deployer, mock_art["bytecode"])
    wall = deploy(deployer, wall_art["bytecode"], ["address"], [mock])
    print(f"Mock registry: {mock}\nAgentWall:     {wall}\n")

    # Align to a clean UTC day boundary (01:00 UTC on the NEXT day,
    # since 01:00 today is already behind the genesis block timestamp).
    now = t.get_block_by_number("latest")["timestamp"]
    day_d = now // DAY + 1
    t.time_travel(day_d * DAY + 3600)
    today = call(t, wall, "currentDay()", [], [], ["uint256"])[0]
    print(f"Chain day index: {today}\n-- day 1 --")

    # Alice + Bob are Agent ID holders; Mallory is not.
    send(deployer, mock, "setBalance(address,uint256)", ["address", "uint256"], [alice, 1])
    send(deployer, mock, "setBalance(address,uint256)", ["address", "uint256"], [bob, 1])

    def expect_revert(frm, sig, types, args):
        """A revert surfaces either as TransactionFailed or as a status-0 receipt."""
        try:
            r = send(frm, wall, sig, types, args)
            return r["status"] == 0
        except TransactionFailed:
            return True

    # 1. non-holder reverts
    check("non-holder check-in reverts", expect_revert(mallory, "checkIn(string)", ["string"], ["gm"]))

    # 2. holder check-in works
    rcpt = send(alice, wall, "checkIn(string)", ["string"], ["gm agents"])
    log = rcpt["logs"][0]
    topic0 = log["topics"][0]
    if isinstance(topic0, str):
        topic0 = bytes.fromhex(topic0[2:])
    check("CheckIn event emitted", topic0 == keccak(text="CheckIn(address,uint256,uint256,string)"))
    check("streakOf(alice) == 1", call(t, wall, "streakOf(address)", ["address"], [alice], ["uint256"])[0] == 1)
    check("bestStreakOf(alice) == 1", call(t, wall, "bestStreakOf(address)", ["address"], [alice], ["uint256"])[0] == 1)
    check("totalCheckInsOf(alice) == 1", call(t, wall, "totalCheckInsOf(address)", ["address"], [alice], ["uint256"])[0] == 1)
    check("hasCheckedInToday(alice)", call(t, wall, "hasCheckedInToday(address)", ["address"], [alice], ["bool"])[0] is True)
    check("global totalCheckIns == 1", call(t, wall, "totalCheckIns()", [], [], ["uint256"])[0] == 1)
    check("uniqueAgents == 1", call(t, wall, "uniqueAgents()", [], [], ["uint256"])[0] == 1)

    # 3. same-day second check-in reverts
    check("same-day second check-in reverts", expect_revert(alice, "checkIn(string)", ["string"], ["again"]))

    # 4. shout length: 141 bytes reverts (use Bob, who has not checked in)
    check("141-byte shout reverts", expect_revert(bob, "checkIn(string)", ["string"], ["x" * 141]))
    send(bob, wall, "checkIn(string)", ["string"], ["y" * 140])
    check("140-byte shout accepted", call(t, wall, "totalCheckInsOf(address)", ["address"], [bob], ["uint256"])[0] == 1)
    check("uniqueAgents == 2 after Bob", call(t, wall, "uniqueAgents()", [], [], ["uint256"])[0] == 2)
    check("global totalCheckIns == 2", call(t, wall, "totalCheckIns()", [], [], ["uint256"])[0] == 2)

    # 5. next consecutive day: Alice streak -> 2
    print("-- day 2 --")
    t.time_travel((day_d + 1) * DAY + 3600)
    send(alice, wall, "checkIn(string)", ["string"], ["day two"])
    check("streak increments to 2 on consecutive day",
          call(t, wall, "streakOf(address)", ["address"], [alice], ["uint256"])[0] == 2)
    check("bestStreakOf(alice) == 2", call(t, wall, "bestStreakOf(address)", ["address"], [alice], ["uint256"])[0] == 2)
    check("hasCheckedInToday(alice) on day 2", call(t, wall, "hasCheckedInToday(address)", ["address"], [alice], ["bool"])[0] is True)
    check("Bob has NOT checked in on day 2", call(t, wall, "hasCheckedInToday(address)", ["address"], [bob], ["bool"])[0] is False)

    # 6. gap day: travel to day 4 (skip day 3) -> streak resets to 1
    print("-- day 4 (day 3 skipped) --")
    t.time_travel((day_d + 3) * DAY + 3600)
    check("streakOf(alice) reads 0 live after gap (before check-in)",
          call(t, wall, "streakOf(address)", ["address"], [alice], ["uint256"])[0] == 0)
    send(alice, wall, "checkIn(string)", ["string"], ["back again"])
    check("streak resets to 1 after gap", call(t, wall, "streakOf(address)", ["address"], [alice], ["uint256"])[0] == 1)
    check("bestStreakOf(alice) still 2", call(t, wall, "bestStreakOf(address)", ["address"], [alice], ["uint256"])[0] == 2)
    check("totalCheckInsOf(alice) == 3", call(t, wall, "totalCheckInsOf(address)", ["address"], [alice], ["uint256"])[0] == 3)
    check("lastCheckInDayOf(alice) == day 4 index",
          call(t, wall, "lastCheckInDayOf(address)", ["address"], [alice], ["uint256"])[0] == day_d + 3)

    # 7. empty shout allowed
    t.time_travel((day_d + 4) * DAY + 3600)
    send(alice, wall, "checkIn(string)", ["string"], [""])
    check("empty shout accepted, streak 2 again",
          call(t, wall, "streakOf(address)", ["address"], [alice], ["uint256"])[0] == 2)

    # 8. revoking the mock Agent ID blocks check-in again
    send(deployer, mock, "setBalance(address,uint256)", ["address", "uint256"], [alice, 0])
    t.time_travel((day_d + 5) * DAY + 3600)
    check("check-in reverts after Agent ID revoked",
          expect_revert(alice, "checkIn(string)", ["string"], ["still here?"]))

    failed = [r for r in results if not r[1]]
    print(f"\n==== {len(results) - len(failed)}/{len(results)} checks passed ====")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
