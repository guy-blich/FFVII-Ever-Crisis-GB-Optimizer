import logging
from dataclasses import dataclass, field

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

        # Stages are listed highest-first so that priority order is preserved.
        # Stage 6 is included from the start to keep its score list in sync as
        # players are consumed, but it starts locked until the unlock condition
        # is met.
        all_stage_nums = sorted(
            (int(k.removeprefix("stage")) for k in bosses_data.root),
            reverse=True,
        )
        self.stages: list[StageState] = [
            StageState(
                num=n,
                scores=score_map[f"stage{n}"],
                hp=bosses_data.root[f"stage{n}"].hp,
                locked=(n == 6),
            )
            for n in all_stage_nums
        ]

        self._stage5_kills = 0

    def optimize(self) -> None:
        respawn_count = 0

        self.logger.info("Starting boss optimization...")

        while self.players:
            if respawn_count != 0:
                self.logger.info(f" *** Bosses on respawn count {respawn_count} ***")

            # Snapshot which stages are active at the start of this round.
            # Stages that unlock mid-round (e.g. stage 6) are not yet expected
            # to be cleared, so they must not affect the end-of-round check.
            round_active = [s for s in self.stages if not s.locked]

            for stage in self.stages:
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
                for stage in self.stages:
                    stage.hp = 100.0
                respawn_count += 1
            else:
                self.logger.info("Not all boss stages could be taken down.")
                break

    def _on_stage5_kill(self) -> None:
        self._stage5_kills += 1
        stage6 = next((s for s in self.stages if s.num == 6), None)
        if stage6 is not None and stage6.locked and self._stage5_kills >= _STAGE6_UNLOCK_AFTER:
            stage6.locked = False
            self.logger.info(f"Stage 6 unlocked after {self._stage5_kills} stage 5 kills!")

    def _remove_used_attempts(self, indices: list[int]) -> None:
        # Always update all stage score lists (including locked ones) so that
        # every list stays aligned with self.players.
        for index in sorted(indices, reverse=True):
            self.players.pop(index)
            for stage in self.stages:
                stage.scores.pop(index)
