import logging
from unittest.mock import patch

import pytest

from src.models.BossData import BossesData
from src.models.PlayerData import PlayersData
from src.optimizer.boss_optimizer import BossOptimizer, _STAGE6_UNLOCK_AFTER


def _make_bosses(hp: float = 100.0, num_stages: int = 6) -> BossesData:
    return BossesData.model_validate(
        {f"stage{i}": {"hp": hp, "deaths": 0} for i in range(1, num_stages + 1)}
    )


def _make_players(**kwargs) -> PlayersData:
    """kwargs: player_name → dict of stage scores + attempts."""
    return PlayersData.model_validate(kwargs)


_FULL_SCORES = dict(
    stage1=100.0, stage2=100.0, stage3=100.0, stage4=100.0, stage5=100.0, stage6=100.0
)
_WEAK_SCORES = dict(stage1=10.0, stage2=8.0, stage3=6.0, stage4=4.0, stage5=2.0, stage6=1.0)

# Patch target for the DP function used inside the optimizer.
_DP_TARGET = "src.optimizer.boss_optimizer.closest_above_100_with_indices"


def _mock_dp(scores: list) -> tuple[float, list[int]]:
    """Stand-in for closest_above_100_with_indices that immediately kills the stage."""
    return (100.0, [0]) if scores else (0.0, [])


class TestBossOptimizerInit:
    def test_stages_in_priority_order(self, simple_boss_data, simple_player_data):
        opt = BossOptimizer(simple_player_data, simple_boss_data)
        assert list(opt.stages.keys()) == [6, 5, 4, 3, 2, 1]

    def test_stage6_starts_locked(self, simple_boss_data, simple_player_data):
        opt = BossOptimizer(simple_player_data, simple_boss_data)
        assert opt.stages[6].locked is True

    def test_stages_1_to_5_start_unlocked(self, simple_boss_data, simple_player_data):
        opt = BossOptimizer(simple_player_data, simple_boss_data)
        unlocked = [s for s in opt.stages.values() if not s.locked]
        assert [s.num for s in unlocked] == [5, 4, 3, 2, 1]

    def test_player_list_length_matches_total_attempts(self, simple_boss_data, simple_player_data):
        # alice: 2 attempts, bob: 2 attempts → 4 total
        opt = BossOptimizer(simple_player_data, simple_boss_data)
        assert len(opt.players) == 4

    def test_scores_length_matches_players(self, simple_boss_data, simple_player_data):
        opt = BossOptimizer(simple_player_data, simple_boss_data)
        for stage in opt.stages.values():
            assert len(stage.scores) == len(opt.players)

    def test_stage_hp_loaded_correctly(self):
        bosses = _make_bosses(hp=75.0)
        players = _make_players(p1={**_FULL_SCORES, "attempts": 1})
        opt = BossOptimizer(players, bosses)
        for stage in opt.stages.values():
            assert stage.hp == 75.0


class TestBossOptimizerOptimize:
    def test_single_player_clears_stages_1_to_5(self, caplog):
        """One player with 100% on all stages and 5 attempts clears stages 1–5."""
        players = _make_players(hero={**_FULL_SCORES, "attempts": 5})
        bosses = _make_bosses(hp=100.0)
        opt = BossOptimizer(players, bosses)
        with caplog.at_level(logging.INFO, logger="src"):
            opt.optimize()
        assert any("All active boss stages" in m for m in caplog.messages)

    def test_not_enough_players_leaves_nonzero_hp(self):
        players = _make_players(weak={**_WEAK_SCORES, "attempts": 1})
        bosses = _make_bosses(hp=100.0)
        opt = BossOptimizer(players, bosses)
        opt.optimize()
        assert any(s.hp > 0.0 for s in opt.stages.values() if not s.locked)

    def test_optimize_removes_used_players(self):
        players = _make_players(p1={**_FULL_SCORES, "attempts": 2})
        bosses = _make_bosses(hp=100.0)
        opt = BossOptimizer(players, bosses)
        initial_count = len(opt.players)
        opt.optimize()
        assert len(opt.players) < initial_count

    def test_stages_optimized_in_priority_order(self, caplog):
        """Stage 5 is processed before stage 1 (stage 6 is locked so skipped)."""
        players = _make_players(p1={**_FULL_SCORES, "attempts": 5})
        bosses = _make_bosses(hp=100.0)
        opt = BossOptimizer(players, bosses)
        with caplog.at_level(logging.INFO, logger="src"):
            opt.optimize()
        stage_mentions = [m for m in caplog.messages if "Boss stage" in m]
        assert "Boss stage 5" in stage_mentions[0]

    def test_locked_stage6_scores_stay_in_sync(self):
        """Stage 6 score list shrinks in lockstep with players even while locked."""
        players = _make_players(p1={**_FULL_SCORES, "attempts": 3})
        bosses = _make_bosses(hp=100.0)
        opt = BossOptimizer(players, bosses)
        opt.optimize()
        stage6 = opt.stages[6]
        assert len(stage6.scores) == len(opt.players)


class TestStage6Unlock:
    """Unit and integration tests for the stage 6 unlock mechanic.

    Integration tests that need many DP calls use _mock_dp to avoid the O(n×S)
    cost of the knapsack algorithm with large player pools.
    """

    def _make_opt(self, num_players: int, attempts: int = 1) -> BossOptimizer:
        players = _make_players(
            **{f"p{i}": {**_FULL_SCORES, "attempts": attempts} for i in range(1, num_players + 1)}
        )
        return BossOptimizer(players, _make_bosses())

    def test_stage6_unlocks_at_threshold(self):
        """_on_stage5_kill() unlocks stage 6 exactly at the threshold."""
        opt = self._make_opt(num_players=1)
        stage6 = opt.stages[6]

        for _ in range(_STAGE6_UNLOCK_AFTER - 1):
            opt._on_stage5_kill()
        assert stage6.locked is True, "should still be locked before threshold"

        opt._on_stage5_kill()
        assert stage6.locked is False, "should unlock at threshold"

    def test_stage6_does_not_unlock_again_once_unlocked(self):
        """Calling _on_stage5_kill() beyond the threshold keeps stage 6 unlocked."""
        opt = self._make_opt(num_players=1)
        stage6 = opt.stages[6]

        for _ in range(_STAGE6_UNLOCK_AFTER + 3):
            opt._on_stage5_kill()
        assert stage6.locked is False

    def test_stage6_unlock_logged(self, caplog):
        """Unlock event is logged at info level."""
        opt = self._make_opt(num_players=1)
        with caplog.at_level(logging.INFO, logger="src"):
            for _ in range(_STAGE6_UNLOCK_AFTER):
                opt._on_stage5_kill()
        assert any("Stage 6 unlocked" in m for m in caplog.messages)

    def test_stage6_not_unlocked_with_insufficient_clears(self):
        """Full optimize run with only 1 round of clears does not unlock stage 6."""
        # 5 players × 1 attempt = 5 total slots; exactly one full round (stages 1–5)
        # → stage5_kills = 1, not enough to unlock.
        with patch(_DP_TARGET, side_effect=_mock_dp):
            opt = self._make_opt(num_players=5)
            opt.optimize()
        stage6 = opt.stages[6]
        assert stage6.locked is True

    def test_stage6_unlocks_during_optimize(self, caplog):
        """After 5 full rounds, stage 6 unlocks inside the optimize loop."""
        # 5 rounds × 5 stages/round = 25 slots to clear stages 1–5 five times,
        # then 6 more for round 6 (stage 6 now included) → 31 total.
        with patch(_DP_TARGET, side_effect=_mock_dp):
            opt = self._make_opt(num_players=31)
            with caplog.at_level(logging.INFO, logger="src"):
                opt.optimize()
        assert any("Stage 6 unlocked" in m for m in caplog.messages)

    def test_stage6_processed_after_unlock(self, caplog):
        """Stage 6 is fought in the round after it is unlocked."""
        with patch(_DP_TARGET, side_effect=_mock_dp):
            opt = self._make_opt(num_players=31)
            with caplog.at_level(logging.INFO, logger="src"):
                opt.optimize()

        msgs = caplog.messages
        unlock_idx = next(i for i, m in enumerate(msgs) if "Stage 6 unlocked" in m)
        stage6_idx = next(i for i, m in enumerate(msgs) if "Boss stage 6" in m)
        assert stage6_idx > unlock_idx

    def test_stage6_is_highest_priority_when_active(self, caplog):
        """Once unlocked, stage 6 appears before stage 5 in each subsequent round."""
        with patch(_DP_TARGET, side_effect=_mock_dp):
            opt = self._make_opt(num_players=31)
            with caplog.at_level(logging.INFO, logger="src"):
                opt.optimize()

        msgs = caplog.messages
        unlock_idx = next(i for i, m in enumerate(msgs) if "Stage 6 unlocked" in m)
        post_unlock = msgs[unlock_idx + 1 :]
        stage6_pos = next(i for i, m in enumerate(post_unlock) if "Boss stage 6" in m)
        stage5_pos = next(i for i, m in enumerate(post_unlock) if "Boss stage 5" in m)
        assert stage6_pos < stage5_pos

    def test_unlock_threshold_constant(self):
        assert _STAGE6_UNLOCK_AFTER == 5


class TestMidBattleInit:
    """Tests for starting the optimizer mid-battle using deaths from boss_data."""

    def _make_bosses_with_deaths(self, stage5_deaths: int) -> BossesData:
        data = {f"stage{i}": {"hp": "100%", "deaths": 0} for i in range(1, 7)}
        data["stage5"]["deaths"] = stage5_deaths
        return BossesData.model_validate(data)

    def _make_players(self, n: int = 1) -> PlayersData:
        return PlayersData.model_validate(
            {f"p{i}": {**_FULL_SCORES, "attempts": 1} for i in range(1, n + 1)}
        )

    def test_stage5_deaths_preseed_kill_counter(self):
        bosses = self._make_bosses_with_deaths(stage5_deaths=3)
        opt = BossOptimizer(self._make_players(), bosses)
        assert opt._stage5_kills == 3

    def test_stage6_stays_locked_when_deaths_below_threshold(self):
        bosses = self._make_bosses_with_deaths(stage5_deaths=_STAGE6_UNLOCK_AFTER - 1)
        opt = BossOptimizer(self._make_players(), bosses)
        assert opt.stages[6].locked is True

    def test_stage6_unlocked_at_init_when_deaths_meet_threshold(self):
        bosses = self._make_bosses_with_deaths(stage5_deaths=_STAGE6_UNLOCK_AFTER)
        opt = BossOptimizer(self._make_players(), bosses)
        assert opt.stages[6].locked is False

    def test_stage6_unlocked_at_init_when_deaths_exceed_threshold(self):
        bosses = self._make_bosses_with_deaths(stage5_deaths=_STAGE6_UNLOCK_AFTER + 2)
        opt = BossOptimizer(self._make_players(), bosses)
        assert opt.stages[6].locked is False

    def test_partial_deaths_unlock_after_fewer_kills(self):
        """With 3 existing deaths, stage 6 unlocks after 2 more stage 5 kills."""
        bosses = self._make_bosses_with_deaths(stage5_deaths=3)
        opt = BossOptimizer(self._make_players(), bosses)
        for _ in range(_STAGE6_UNLOCK_AFTER - 3 - 1):
            opt._on_stage5_kill()
        assert opt.stages[6].locked is True
        opt._on_stage5_kill()
        assert opt.stages[6].locked is False
