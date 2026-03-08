import pytest
from src.models.BossData import BossesData
from src.models.PlayerData import PlayersData


@pytest.fixture
def simple_boss_data() -> BossesData:
    return BossesData.model_validate({f"stage{i}": {"hp": 100.0, "deaths": 0} for i in range(1, 7)})


@pytest.fixture
def simple_player_data() -> PlayersData:
    return PlayersData.model_validate(
        {
            "alice": {
                "stage1": 60.0,
                "stage2": 50.0,
                "stage3": 40.0,
                "stage4": 30.0,
                "stage5": 20.0,
                "stage6": 10.0,
                "attempts": 2,
            },
            "bob": {
                "stage1": 55.0,
                "stage2": 70.0,
                "stage3": 45.0,
                "stage4": 35.0,
                "stage5": 25.0,
                "stage6": 12.0,
                "attempts": 2,
            },
        }
    )
