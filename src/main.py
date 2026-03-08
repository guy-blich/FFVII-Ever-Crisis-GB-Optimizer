import argparse
from pathlib import Path

from src.models.BossData import BossesData
from src.models.PlayerData import PlayersData
from src.optimizer.boss_optimizer import BossOptimizer
from src.utils.file_utils import get_json_data
from src.utils.logger import setup_logger

_DEFAULT_CONFIG = Path("config")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="guild-battle-optimizer",
        description="Optimal player assignment for FF7 Ever Crisis Guild Battles.",
    )
    parser.add_argument(
        "--players",
        "-p",
        type=Path,
        default=_DEFAULT_CONFIG / "player_data.json",
        metavar="FILE",
        help="Path to the player data JSON file (default: config/player_data.json)",
    )
    parser.add_argument(
        "--bosses",
        "-b",
        type=Path,
        default=_DEFAULT_CONFIG / "boss_data.json",
        metavar="FILE",
        help="Path to the boss data JSON file (default: config/boss_data.json)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        metavar="LEVEL",
        help="Logging verbosity (default: INFO)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    setup_logger(level=args.log_level)

    players_data = PlayersData.model_validate(get_json_data(args.players))
    bosses_data = BossesData.model_validate(get_json_data(args.bosses))

    optimizer = BossOptimizer(players_data, bosses_data)
    optimizer.optimize()


if __name__ == "__main__":
    main()
