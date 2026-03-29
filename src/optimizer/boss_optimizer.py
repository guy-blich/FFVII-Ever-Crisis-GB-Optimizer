import logging
from dataclasses import dataclass

from src.models.BossData import BossesData
from src.models.PlayerData import PlayersData
from src.utils.data_utils import create_score_lists, closest_above_100_with_indices

# Stage 6 unlocks after stage 5 has been beaten this many times in total.
_STAGE6_UNLOCK_AFTER = 5


@dataclass
class StageState:
    num: int
    scores: list[float]
    hp: float
    locked: bool = False


class BossOptimizer:

    def __init__(self, players_data: PlayersData, bosses_data: BossesData) -> None:
        self.logger = logging.getLogger(__name__)

        score_map, self.players = create_score_lists(players_data.model_dump())

        self.stages: dict[int, StageState] = {
            n: StageState(
                num=n,
                scores=score_map[f"stage{n}"],
                hp=bosses_data.root[f"stage{n}"].hp,
                locked=(n == 6),
            )
            for n in sorted(
                (int(k.removeprefix("stage")) for k in bosses_data.root),
                reverse=True,
            )
        }

        self._stage5_kills = 0

    def optimize(self) -> None:
        respawn_count = 0

        self.logger.info("Starting boss optimization...")

        while self.players:
            if respawn_count != 0:
                self.logger.info(f" *** Bosses on respawn count {respawn_count} ***")

            # Snapshot active stages before the round so a mid-round unlock
            # (stage 6) doesn't affect this round's clear check.
            round_active = [s for s in self.stages.values() if not s.locked]

            for stage in self.stages.values():
                if stage.locked:
                    continue

                result_sum, result_indices = closest_above_100_with_indices(stage.scores)
                stage.hp -= result_sum

                player_names = [self.players[i] for i in result_indices]
                if stage.hp <= 0:
                    stage.hp = 0.0
                    self.logger.info(
                        f"Boss stage {stage.num} efficiently killed by {player_names} "
                        f"with a sum of {result_sum:.2f}%"
                    )
                    if stage.num == 5:
                        self._on_stage5_kill()
                else:
                    self.logger.info(
                        f"Boss stage {stage.num} taken to {stage.hp:.2f}% HP remaining "
                        f"by {player_names} with a sum of {result_sum:.2f}%"
                    )

                self._remove_used_attempts(result_indices)

            if all(s.hp == 0.0 for s in round_active):
                self.logger.info("All active boss stages have been taken down!")
                for stage in self.stages.values():
                    stage.hp = 100.0
                respawn_count += 1
            else:
                self.logger.info("Not all boss stages could be taken down.")
                break

    def _on_stage5_kill(self) -> None:
        self._stage5_kills += 1
        stage6 = self.stages.get(6)
        if stage6 is not None and stage6.locked and self._stage5_kills >= _STAGE6_UNLOCK_AFTER:
            stage6.locked = False
            self.logger.info(f"Stage 6 unlocked after {self._stage5_kills} stage 5 kills!")

    def _remove_used_attempts(self, indices: list[int]) -> None:
        # Update all lists including locked stages to keep them aligned with self.players.
        for index in sorted(indices, reverse=True):
            self.players.pop(index)
            for stage in self.stages.values():
                stage.scores.pop(index)
