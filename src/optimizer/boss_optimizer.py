import logging

from src.models.BossData import BossesData
from src.models.PlayerData import PlayersData
from src.utils.data_utils import create_score_lists, closest_above_100_with_indices


class BossOptimizer:

    def __init__(self, players_data: PlayersData, bosses_data: BossesData) -> None:
        """
        Initializes the BossOptimizer class
        :param players_data: Data model for all players/guild members
        :param bosses_data: Data model for all boss stages
        """
        self.logger = logging.getLogger(__name__)
        self.bosses_data = bosses_data

        # Create lists of player scores and attempts that have the same order as the
        # players, to easily calculate and iterate, while still keeping track of which
        # score is which player's, since the player name and their scores share the same
        # index in the lists.
        # Potentially, duplicates of player names and scores could
        # be added, in accordance to the amount of attempts the player has.
        (
            self.players,
            stage1_scores,
            stage2_scores,
            stage3_scores,
            stage4_scores,
            stage5_scores,
            # players_data.model_dump() converts the data model to a dictionary
        ) = create_score_lists(players_data.model_dump())

        self.stages_scores = [
            stage5_scores,
            stage4_scores,
            stage3_scores,
            stage2_scores,
            stage1_scores,
        ]

        self.stages_hp = []

        for stage in self.bosses_data.root.values():
            self.stages_hp.append(stage.hp)

    def optimize(self) -> None:
        """
        Optimizes boss fights based on player and boss data models
        """
        # Keeps track of the amount of boss respawns
        respawn_count = 0

        # Keeps track of all the of the boss stage HPs

        self.logger.info("Starting boss optimization...")

        while len(self.players) > 0:

            if respawn_count != 0:
                self.logger.info(f" *** Bosses on respawn count {respawn_count} ***")

            # Optimizes each stage from 5 to 1, since the higher the stage, the more
            # score and difficulty the boss fight will have, which means higher stages
            # will always be prioritized over lower stages
            for i, stage_scores in enumerate(self.stages_scores):
                result_sum, result_indices = self.optimize_stage(stage_scores)
                self.stages_hp[i] -= result_sum

                # Shows different messages depending on whether the boss stage is
                # efficiently killed or not
                if self.stages_hp[i] <= 0:
                    self.logger.info(
                        f"Boss stage {i + 1} can be efficiently killed by the "
                        f"players: {[self.players[result_index] 
                                     for result_index in result_indices]} "
                        f"with a sum of {result_sum}%"
                    )
                    self.stages_hp[i] = 0.0
                else:
                    self.logger.info(
                        f"Boss stage {i + 1} can be taken down to {self.stages_hp[i]}% "
                        f"by the players: {[self.players
                        [result_index] for result_index in result_indices]} "
                        f"with a sum of {result_sum}%"
                    )

                self.remove_used_attempts(result_indices)

            if sum(self.stages_hp) == 0:
                self.logger.info("All boss stages have been taken down 😁")
                # The [1] at the end of the enumerate() is to skip the first element,
                # since the objective is to edit the value, and we don't need to get it
                for index, hp in enumerate(self.stages_hp):
                    self.stages_hp[index] = 100.0
                respawn_count += 1
            else:
                self.logger.info("Not all boss stages were able to be taken down 😕")
                break

    def optimize_stage(self, scores: list) -> tuple[float, list[int]]:
        """
        Optimizes a specific stage of the boss fight
        :param scores: List of player scores for the current stage
        """
        # Since there are multiple attempts for each player, we need to create a version

        # Calculates the sum of the scores and the indices of the scores that pass 100%
        # and are the closest to 100%, or the sum of the scores if they don't pass 100%
        result_sum, result_indices = closest_above_100_with_indices(scores)

        return result_sum, result_indices

    def remove_used_attempts(self, indices: list) -> None:
        """
        Removes the used attempts from all the lists (players, stages scores, etc.)
        :param indices: List of indices of the players that were used
        """
        indices.sort(reverse=True)
        for index in indices:
            self.players.pop(index)
            for i, stage_scores in enumerate(self.stages_scores):
                stage_scores.pop(index)
