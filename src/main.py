from src.models.BossData import BossesData
from src.models.PlayerData import PlayersData
from src.optimizer.boss_optimizer import BossOptimizer
from src.utils.file_utils import get_json_data
from src.utils.logger import setup_logger


def main() -> None:
    """Main function"""
    setup_logger()

    # Get data models from JSON files and validate them using pydantic models
    players_data = PlayersData.model_validate(
        get_json_data(file_name="player_data.json")
    )
    bosses_data = BossesData.model_validate(get_json_data(file_name="boss_data.json"))
    optimizer = BossOptimizer(players_data, bosses_data)
    optimizer.optimize()


if __name__ == "__main__":
    main()
