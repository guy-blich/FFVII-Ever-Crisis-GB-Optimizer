def create_score_lists(players_data: dict) -> tuple:
    """
    Creates lists of player scores and attempts that have the same order as the players, to easily
    calculate and iterate, while still keeping track of which score is which player's,
    since the player name and their scores share the same index in the lists

    Potentially, duplicates of player names and scores could be added, in accordance to the amount of attempts the
    player has
    :param players_data: Dictionary of player data
    """

    players = []
    stage1_scores = []
    stage2_scores = []
    stage3_scores = []
    stage4_scores = []
    stage5_scores = []

    for player_name, player_data in players_data.items():
        for i in range(player_data["attempts"]):
            players.append(player_name)
            stage1_scores.append(player_data["stage1"])
            stage2_scores.append(player_data["stage2"])
            stage3_scores.append(player_data["stage3"])
            stage4_scores.append(player_data["stage4"])
            stage5_scores.append(player_data["stage5"])

    return (
        players,
        stage1_scores,
        stage2_scores,
        stage3_scores,
        stage4_scores,
        stage5_scores,
    )


def closest_above_100_with_indices(scores: list) -> tuple[float, list[int]]:
    """
    Finds the closest score to 100% and returns the sum of the scores and the indices of the scores that pass 100%
    :param scores: List of player scores
    """
    target = 100
    scaling_factor = 1000  # Scaling factor to convert percentages to integers
    scaled_scores = [int(p * scaling_factor) for p in scores]
    total_sum = sum(scaled_scores)

    # Handle the case with only one option separately
    if len(scaled_scores) == 1:
        if scaled_scores[0] >= target * scaling_factor:
            return scaled_scores[0] / scaling_factor, [0]
        else:
            return scaled_scores[0] / scaling_factor, [0]

    # Dynamic programming table: to track possible sums
    _INF = total_sum + 1  # A value representing an unreachable sum
    # Initialize DP arrays:
    dp = [_INF] * (total_sum + 1)
    dp[0] = 0  # A sum of 0 requires no elements

    # To track the indices that lead to each sum
    selected_indices = [[] for _ in range(len(dp))]

    # Process each percentage
    for i, score in enumerate(scaled_scores):
        for j in range(len(dp) - 1, score - 1, -1):
            if dp[j - int(score)] + score < dp[j]:
                dp[j] = dp[j - int(score)] + score
                selected_indices[j] = selected_indices[j - int(score)].copy()
                selected_indices[j].append(i)

    # Now, find the smallest sum >= 100, if exists
    best_sum = _INF
    best_indices = []
    target_scaled = target * scaling_factor  # 100% scaled to integer
    for i in range(target_scaled, len(dp)):
        if dp[i] <= total_sum:
            best_sum = dp[i]
            best_indices = selected_indices[i]
            break

    # If no sum >= 100 is found, return the largest sum and the corresponding indices
    if best_sum == _INF:
        best_sum = max(dp)
        best_indices = selected_indices[dp.index(best_sum)]

    # Convert the best sum back to a percentage
    best_sum_percentage = best_sum / scaling_factor
    return best_sum_percentage, best_indices
