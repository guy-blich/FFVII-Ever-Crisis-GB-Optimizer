import pytest
from pydantic import ValidationError

from src.models.BossData import BossData, BossesData
from src.models.PlayerData import PlayerData, PlayersData

_PLAYER_DEFAULTS = dict(
    stage1=100.0, stage2=80.0, stage3=60.0, stage4=40.0, stage5=20.0, stage6=10.0
)


class TestBossData:
    def test_numeric_hp(self):
        boss = BossData(hp=75.5, deaths=0)
        assert boss.hp == 75.5

    def test_percentage_string_hp(self):
        boss = BossData.model_validate({"hp": "82%", "deaths": 0})
        assert boss.hp == 82.0

    def test_full_hp(self):
        boss = BossData.model_validate({"hp": "100%", "deaths": 0})
        assert boss.hp == 100.0

    def test_invalid_hp_type(self):
        with pytest.raises(ValidationError):
            BossData(hp="not-a-number", deaths=0)


class TestBossesData:
    def test_all_six_stages(self):
        data = BossesData.model_validate(
            {f"stage{i}": {"hp": float(i * 10), "deaths": 0} for i in range(1, 7)}
        )
        assert data.root["stage3"].hp == 30.0
        assert data.root["stage6"].hp == 60.0
        assert len(data.root) == 6

    def test_percentage_hp_in_all_stages(self):
        data = BossesData.model_validate(
            {f"stage{i}": {"hp": "100%", "deaths": 0} for i in range(1, 7)}
        )
        for stage in data.root.values():
            assert stage.hp == 100.0


class TestPlayerData:
    def test_numeric_stages(self):
        player = PlayerData(**_PLAYER_DEFAULTS, attempts=3)
        assert player.stage5 == 20.0
        assert player.stage6 == 10.0

    def test_percentage_string_stages(self):
        player = PlayerData.model_validate(
            {
                "stage1": "50%",
                "stage2": "30%",
                "stage3": "10%",
                "stage4": "5%",
                "stage5": "2%",
                "stage6": "1%",
                "attempts": 1,
            }
        )
        assert player.stage1 == 50.0
        assert player.stage6 == 1.0

    def test_invalid_attempts(self):
        with pytest.raises(ValidationError):
            PlayerData(**_PLAYER_DEFAULTS, attempts="three")


class TestPlayersData:
    def test_multiple_players(self):
        data = PlayersData.model_validate(
            {
                "p1": {
                    "stage1": 100.0,
                    "stage2": 100.0,
                    "stage3": 50.0,
                    "stage4": 25.0,
                    "stage5": 10.0,
                    "stage6": 5.0,
                    "attempts": 3,
                },
                "p2": {
                    "stage1": "80%",
                    "stage2": "60%",
                    "stage3": "40%",
                    "stage4": "20%",
                    "stage5": "5%",
                    "stage6": "2%",
                    "attempts": 2,
                },
            }
        )
        assert data.root["p1"].attempts == 3
        assert data.root["p1"].stage6 == 5.0
        assert data.root["p2"].stage1 == 80.0
        assert data.root["p2"].stage6 == 2.0
