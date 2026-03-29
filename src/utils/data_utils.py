from typing import Any


def create_score_lists(
    players_data: dict[str, Any],
) -> tuple[dict[str, list[float]], list[str]]:
    """
    Expands each player by their attempt count into parallel score lists.
    Returns a dict mapping stage key → scores, and the corresponding player name list.
    """
    first_player = next(iter(players_data.values()))
    stage_keys = sorted(
        (k for k in first_player if k.startswith("stage")),
        key=lambda k: int(k.removeprefix("stage")),
    )

    players: list[str] = []
    scores: dict[str, list[float]] = {key: [] for key in stage_keys}

    for player_name, player_data in players_data.items():
        for _ in range(player_data["attempts"]):
            players.append(player_name)
            for key in stage_keys:
                scores[key].append(player_data[key])

    return scores, players


def closest_above_100_with_indices(scores: list[float]) -> tuple[float, list[int]]:
    """
    0/1 knapsack: finds the minimum subset of scores summing to >= 100.
    Falls back to the largest reachable sum if 100 is not achievable.
    Scores are scaled to integers to avoid floating-point issues.
    """
    if not scores:
        return 0.0, []

    # Multiply by 1000 so fractional percentages (e.g. 63.5%) become integers.
    # The DP works on integer indices, so floating-point scores must be scaled first.
    scaling_factor = 1000
    scaled = [int(s * scaling_factor) for s in scores]
    total = sum(scaled)
    target = 100 * scaling_factor

    # dp[j] answers "what is the smallest sum of selected players that lands exactly
    # on j?". Most entries start at _INF (unreachable). dp[0] = 0 because using
    # nobody deals exactly 0%.
    _INF = total + 1
    dp = [_INF] * (total + 1)
    dp[0] = 0

    # pred[j] = (prev_j, player_index): records which player was added last to reach
    # sum j, and what the sum was before adding them. Used to reconstruct the player
    # list after the DP without storing full index lists at every cell.
    pred: list[tuple[int, int] | None] = [None] * (total + 1)

    for i, score in enumerate(scaled):
        # Iterate backwards so each player can only be selected once (0/1 knapsack).
        # Going forwards would allow the same player to be picked multiple times.
        for j in range(total, score - 1, -1):
            candidate = dp[j - score] + score
            if candidate < dp[j]:
                dp[j] = candidate
                pred[j] = (j - score, i)

    def _backtrack(j: int) -> list[int]:
        # Follow the pred chain from target sum back to 0, collecting the player
        # index added at each step.
        indices: list[int] = []
        entry = pred[j]
        while entry is not None:
            prev_j, item_i = entry
            indices.append(item_i)
            j = prev_j
            entry = pred[j]
        return indices

    # Return the minimum reachable sum >= 100%, or the best available if 100% is
    # not achievable (e.g. not enough players left to kill the stage).
    for j in range(target, total + 1):
        if dp[j] <= total:
            return dp[j] / scaling_factor, _backtrack(j)

    best_j = max((j for j in range(total + 1) if dp[j] <= total), default=0)
    return dp[best_j] / scaling_factor, _backtrack(best_j)
