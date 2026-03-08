def create_score_lists(
    players_data: dict,
) -> tuple[dict[str, list[float]], list[str]]:
    """
    Builds parallel lists of player names and per-stage scores, expanding each
    player's entry by their number of attempts so that each attempt is treated
    as an independent slot.

    Stage keys are detected from the data, so adding a new stage only requires
    updated config files and model fields — no code changes here.

    Returns a dict mapping stage key → list of scores, and the corresponding
    player name list (same length and order as each score list).
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
    Finds the minimum subset of scores whose sum is >= 100 (closest kill).
    Falls back to the largest achievable sum when 100 cannot be reached.

    Uses a 0/1 knapsack DP scaled to integers to avoid floating-point issues.
    Returns (sum_percentage, list_of_indices).
    """
    if not scores:
        return 0.0, []

    scaling_factor = 1000
    scaled = [int(s * scaling_factor) for s in scores]
    total = sum(scaled)
    target = 100 * scaling_factor

    # dp[j] = smallest sum of selected items that equals exactly j, or _INF if unreachable
    _INF = total + 1
    dp = [_INF] * (total + 1)
    dp[0] = 0
    selected_indices: list[list[int]] = [[] for _ in range(total + 1)]

    for i, score in enumerate(scaled):
        for j in range(total, score - 1, -1):
            candidate = dp[j - score] + score
            if candidate < dp[j]:
                dp[j] = candidate
                selected_indices[j] = selected_indices[j - score] + [i]

    # Find the minimum sum >= target
    for j in range(target, total + 1):
        if dp[j] <= total:
            return dp[j] / scaling_factor, selected_indices[j]

    # No combination reaches 100%; return the largest reachable sum
    best_j = max((j for j in range(total + 1) if dp[j] <= total), default=0)
    return dp[best_j] / scaling_factor, selected_indices[best_j]
