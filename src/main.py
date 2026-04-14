import argparse
from pathlib import Path
from typing import Any

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
        "--source",
        choices=["json", "csv", "sheets"],
        default="json",
        metavar="SOURCE",
        help="Data source: 'json', 'csv', or 'sheets'. Default: json",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        metavar="LEVEL",
        help="Logging verbosity (default: INFO)",
    )

    file_group = parser.add_argument_group("JSON/CSV source options")
    file_group.add_argument(
        "--players",
        "-p",
        type=Path,
        default=_DEFAULT_CONFIG / "player_data.json",
        metavar="FILE",
        help="Path to player data file (default: config/player_data.json)",
    )
    file_group.add_argument(
        "--bosses",
        "-b",
        type=Path,
        default=_DEFAULT_CONFIG / "boss_data.json",
        metavar="FILE",
        help="Path to boss data file (default: config/boss_data.json)",
    )

    sheets_group = parser.add_argument_group("Google Sheets source options")
    sheets_group.add_argument(
        "--sheet-id",
        metavar="ID",
        help="Google Sheet ID (found in the sheet URL)",
    )
    sheets_group.add_argument(
        "--credentials",
        type=Path,
        default=Path("credentials.json"),
        metavar="FILE",
        help="Path to service account credentials JSON (default: credentials.json)",
    )
    sheets_group.add_argument(
        "--players-tab",
        default="Players",
        metavar="TAB",
        help="Sheet tab name for player data (default: Players)",
    )
    sheets_group.add_argument(
        "--bosses-tab",
        default="Bosses",
        metavar="TAB",
        help="Sheet tab name for boss data (default: Bosses)",
    )

    return parser.parse_args()


def _load_from_json(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    return get_json_data(args.players), get_json_data(args.bosses)


def _load_from_csv(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.utils.csv_utils import get_player_data, get_boss_data

    return get_player_data(args.players), get_boss_data(args.bosses)


def _load_from_sheets(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.utils.sheets_utils import open_sheet, get_player_data, get_boss_data

    if not args.sheet_id:
        raise SystemExit(
            "error: --sheet-id is required when using --source sheets\n"
            "  Example: --sheet-id 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
        )
    sheet = open_sheet(args.sheet_id, args.credentials)
    return get_player_data(sheet, args.players_tab), get_boss_data(sheet, args.bosses_tab)


_LOADERS = {
    "json": _load_from_json,
    "csv": _load_from_csv,
    "sheets": _load_from_sheets,
}


def main() -> None:
    args = _parse_args()
    setup_logger(level=args.log_level)

    players_raw, bosses_raw = _LOADERS[args.source](args)

    players_data = PlayersData.model_validate(players_raw)
    bosses_data = BossesData.model_validate(bosses_raw)

    optimizer = BossOptimizer(players_data, bosses_data)
    optimizer.optimize()


if __name__ == "__main__":
    main()
