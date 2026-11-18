// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @notice TEST-ONLY mock of the Agent ID registry. Lets the test harness
///         grant/revoke "Agent ID holder" status by setting a balance.
///         Never deployed to mainnet; AgentWall points at the real
///         registry address in production.
contract MockAgentIdRegistry {
    mapping(address => uint256) private _balances;

    function setBalance(address who, uint256 amount) external {
        _balances[who] = amount;
    }

    function balanceOf(address who) external view returns (uint256) {
        return _balances[who];
    }
}
