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

    # Scale by 100 so two-decimal percentages (e.g. 63.5%, 1.27%) become integers.
    # round() avoids int() truncation from floating-point imprecision (e.g. 1.27*100 = 126.99...).
    scaling_factor = 100
    scaled = [round(s * scaling_factor) for s in scores]
    target = 100 * scaling_factor
    total = sum(scaled)

    # Cap the DP table at target + max(scaled) instead of total.
    # Proof: if S is the minimum reachable sum >= target, removing the last item added
    # (call its value x) yields a sum S - x < target, so S < target + x <= target + max(scaled).
    # Nothing above that bound can ever be the minimum, so tracking it wastes time and memory.
    # This keeps the inner loop O(n * target) rather than O(n * total) — critical when many
    # players score 100% and total would otherwise be orders of magnitude larger than target.
    cap = min(total, target + max(scaled))

    _INF = cap + 1
    dp = [_INF] * (cap + 1)
    dp[0] = 0

    # pred[j] = (prev_j, player_index): records which player was added last to reach
    # sum j, and what the sum was before adding them. Used to reconstruct the player
    # list after the DP without storing full index lists at every cell.
    pred: list[tuple[int, int] | None] = [None] * (cap + 1)

    for i, score in enumerate(scaled):
        # Iterate backwards so each player can only be selected once (0/1 knapsack).
        # Going forwards would allow the same player to be picked multiple times.
        for j in range(min(cap, total), score - 1, -1):
            prev = j - score
            if prev < 0 or dp[prev] >= _INF:
                continue
            candidate = dp[prev] + score
            if candidate < dp[j]:
                dp[j] = candidate
                pred[j] = (prev, i)

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
    for j in range(target, cap + 1):
        if dp[j] < _INF:
            return dp[j] / scaling_factor, _backtrack(j)

    best_j = max((j for j in range(cap + 1) if dp[j] < _INF), default=0)
    return dp[best_j] / scaling_factor, _backtrack(best_j)
