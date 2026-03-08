import pytest
from src.utils.data_utils import create_score_lists, closest_above_100_with_indices

_BASE_PLAYER = dict(stage1=80.0, stage2=60.0, stage3=40.0, stage4=20.0, stage5=10.0, stage6=5.0)


class TestCreateScoreLists:
    def test_single_player_single_attempt(self):
        data = {"alice": {**_BASE_PLAYER, "attempts": 1}}
        scores, players = create_score_lists(data)
        assert players == ["alice"]
        assert scores["stage1"] == [80.0]
        assert scores["stage6"] == [5.0]

    def test_attempts_expand_entries(self):
        data = {"bob": {**_BASE_PLAYER, "stage1": 50.0, "attempts": 3}}
        scores, players = create_score_lists(data)
        assert players == ["bob", "bob", "bob"]
        assert scores["stage1"] == [50.0, 50.0, 50.0]

    def test_multiple_players(self):
        data = {
            "alice": {**_BASE_PLAYER, "stage1": 60.0, "attempts": 1},
            "bob": {**_BASE_PLAYER, "stage1": 55.0, "attempts": 2},
        }
        scores, players = create_score_lists(data)
        assert len(players) == 3
        assert players[0] == "alice"
        assert players[1] == players[2] == "bob"
        assert scores["stage1"] == [60.0, 55.0, 55.0]

    def test_all_stage_keys_present(self):
        data = {"p": {**_BASE_PLAYER, "attempts": 1}}
        scores, _ = create_score_lists(data)
        assert set(scores.keys()) == {"stage1", "stage2", "stage3", "stage4", "stage5", "stage6"}

    def test_stage6_scores_included(self):
        data = {"hero": {**_BASE_PLAYER, "stage6": 99.0, "attempts": 2}}
        scores, players = create_score_lists(data)
        assert scores["stage6"] == [99.0, 99.0]
        assert len(players) == 2


class TestClosestAbove100:
    def test_empty_list(self):
        total, indices = closest_above_100_with_indices([])
        assert total == 0.0
        assert indices == []

    def test_single_player_above_100(self):
        total, indices = closest_above_100_with_indices([100.0])
        assert total == 100.0
        assert indices == [0]

    def test_single_player_below_100(self):
        total, indices = closest_above_100_with_indices([75.0])
        assert total == 75.0
        assert indices == [0]

    def test_two_players_reach_100_exactly(self):
        total, indices = closest_above_100_with_indices([50.0, 50.0])
        assert total == pytest.approx(100.0)
        assert set(indices) == {0, 1}

    def test_finds_minimum_combination_above_100(self):
        # 70 + 40 = 110, but neither alone is enough; that's the only option above 100
        scores = [70.0, 40.0, 20.0]
        total, indices = closest_above_100_with_indices(scores)
        assert total >= 100.0
        assert sum(scores[i] for i in indices) == pytest.approx(total)

    def test_prefers_closest_sum_above_100(self):
        # 60 + 45 = 105, 60 + 50 = 110 — should pick 105 (closer to 100)
        scores = [60.0, 45.0, 50.0]
        total, indices = closest_above_100_with_indices(scores)
        assert total == pytest.approx(105.0)

    def test_no_combination_reaches_100(self):
        scores = [30.0, 25.0, 20.0]
        total, indices = closest_above_100_with_indices(scores)
        assert total == pytest.approx(75.0)
        assert len(indices) > 0

    def test_single_player_over_100(self):
        total, indices = closest_above_100_with_indices([150.0])
        assert total == pytest.approx(150.0)
        assert indices == [0]

    def test_returns_valid_indices(self):
        scores = [55.0, 48.0, 60.0, 30.0]
        total, indices = closest_above_100_with_indices(scores)
        assert all(0 <= i < len(scores) for i in indices)
        assert sum(scores[i] for i in indices) == pytest.approx(total)
