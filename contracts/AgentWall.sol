// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @notice Minimal read interface for the SPACE ID Agent ID registry
///         (BNB Chain mainnet: 0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F).
///         Agent ID is a non-transferable ERC-721; holding one token means
///         the address owns an Agent ID (a name.ai identity).
interface IAgentIDRegistry {
    function balanceOf(address owner) external view returns (uint256);
}

/// @title AgentWall — a daily roll-call wall for Agent ID holders
/// @notice Every day, each Agent ID holder can check in exactly once and
///         leave a short shout. Consecutive daily check-ins build a streak.
///         The wall is gated by Agent ID itself: the holder check runs
///         against the official registry inside checkIn(), so membership
///         IS the product's core flow — no separate sign-up exists.
///
/// @dev DESIGN GUARANTEES (deliberate, part of the audit surface):
///      - NO owner and NO admin functions. Nobody can pause, edit, or
///        remove check-ins — including the deployer.
///      - NO funds: every function is non-payable and the contract can
///        never receive, hold, or move BNB or tokens.
///      - NO approvals are ever requested from users; checkIn() is a
///        plain transaction the user confirms in their own wallet.
///      - NO upgradeability / proxy: the deployed bytecode is final.
///      - Shouts are emitted in events only, never stored, to keep the
///        check-in cheap and the state minimal.
contract AgentWall {
    /// @notice The official Agent ID registry this wall is gated by.
    IAgentIDRegistry public immutable agentIdRegistry;

    /// @notice Total check-ins ever recorded on the wall.
    uint256 public totalCheckIns;

    /// @notice Number of distinct Agent ID addresses that have ever checked in.
    uint256 public uniqueAgents;

    struct AgentStats {
        uint256 streak; // consecutive-day streak as of the last check-in
        uint256 bestStreak; // highest streak ever reached
        uint256 totalCheckIns; // this agent's lifetime check-ins
        uint256 lastCheckInDay; // UTC day index of last check-in (0 = never)
    }

    mapping(address => AgentStats) private _stats;

    /// @notice Emitted on every check-in. Frontends build the wall feed and
    ///         the leaderboard purely from these logs.
    /// @param user The Agent ID holder who checked in.
    /// @param day UTC day index (block.timestamp / 86400).
    /// @param streak The user's current consecutive-day streak after this check-in.
    /// @param shout Optional message, max 140 bytes. Emitted, never stored.
    event CheckIn(address indexed user, uint256 day, uint256 streak, string shout);

    constructor(address registry_) {
        require(registry_ != address(0), "AgentWall: registry required");
        agentIdRegistry = IAgentIDRegistry(registry_);
    }

    /// @notice The current UTC day index used for all daily logic.
    function currentDay() public view returns (uint256) {
        return block.timestamp / 1 days;
    }

    /// @notice True if `user` currently holds an Agent ID.
    function hasAgentId(address user) public view returns (bool) {
        return agentIdRegistry.balanceOf(user) > 0;
    }

    /// @notice Check in for today. Agent ID holders only, once per UTC day.
    /// @param shout Optional message (max 140 bytes), emitted in the event.
    function checkIn(string calldata shout) external {
        require(hasAgentId(msg.sender), "Agent ID required");
        require(bytes(shout).length <= 140, "Shout too long: max 140 bytes");

        uint256 today = currentDay();
        AgentStats storage s = _stats[msg.sender];
        require(s.lastCheckInDay != today, "Already checked in today");

        if (s.totalCheckIns == 0) {
            uniqueAgents += 1;
        }

        // Consecutive day extends the streak; any gap restarts it at 1.
        if (s.lastCheckInDay != 0 && s.lastCheckInDay == today - 1) {
            s.streak += 1;
        } else {
            s.streak = 1;
        }
        if (s.streak > s.bestStreak) {
            s.bestStreak = s.streak;
        }

        s.totalCheckIns += 1;
        s.lastCheckInDay = today;
        totalCheckIns += 1;

        emit CheckIn(msg.sender, today, s.streak, shout);
    }

    /// @notice Current streak of `user`, evaluated live: a streak whose last
    ///         check-in is older than yesterday has already lapsed and reads 0.
    function streakOf(address user) external view returns (uint256) {
        AgentStats storage s = _stats[user];
        if (s.totalCheckIns == 0) return 0;
        if (s.lastCheckInDay + 1 < currentDay()) return 0; // chain broken
        return s.streak;
    }

    /// @notice Highest streak `user` has ever reached.
    function bestStreakOf(address user) external view returns (uint256) {
        return _stats[user].bestStreak;
    }

    /// @notice Lifetime check-ins of `user`.
    function totalCheckInsOf(address user) external view returns (uint256) {
        return _stats[user].totalCheckIns;
    }

    /// @notice UTC day index of `user`'s last check-in (0 = never).
    function lastCheckInDayOf(address user) external view returns (uint256) {
        return _stats[user].lastCheckInDay;
    }

    /// @notice True if `user` has already checked in today (UTC).
    function hasCheckedInToday(address user) external view returns (bool) {
        return _stats[user].totalCheckIns > 0 && _stats[user].lastCheckInDay == currentDay();
    }

    /// @notice Convenience bundle for frontends: (live streak, best streak,
    ///         lifetime check-ins, last check-in day).
    function statsOf(address user)
        external
        view
        returns (uint256 streak, uint256 bestStreak, uint256 total, uint256 lastDay)
    {
        AgentStats storage s = _stats[user];
        streak = this.streakOf(user);
        bestStreak = s.bestStreak;
        total = s.totalCheckIns;
        lastDay = s.lastCheckInDay;
    }
}
