import csv
from pathlib import Path
from typing import Any

_PLAYER_COLUMNS = {"player", "stage1", "stage2", "stage3", "stage4", "stage5", "stage6", "attempts"}
_BOSS_COLUMNS = {"stage", "hp"}


def _normalize(row: Any) -> dict[str, Any]:
    return {k.lower().replace(" ", ""): v for k, v in row.items()}


def _check_headers(found: set[str], required: set[str], path: Path) -> None:
    missing = required - found
    if missing:
        raise SystemExit(
            f"error: {path} is missing required columns: {', '.join(sorted(missing))}\n"
            f"  Found: {', '.join(sorted(found))}"
        )


def get_player_data(path: Path) -> dict[str, Any]:
    """Read a players CSV and return a player_data dict. Headers are case-insensitive."""
    players: dict[str, Any] = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not rows:
            return players
        headers = {k.lower().replace(" ", "") for k in rows[0].keys()}
        _check_headers(headers, _PLAYER_COLUMNS, path)
        for row in rows:
            row = _normalize(row)
            name = str(row["player"]).strip()
            if not name:
                continue
            players[name] = {
                "stage1": row["stage1"],
                "stage2": row["stage2"],
                "stage3": row["stage3"],
                "stage4": row["stage4"],
                "stage5": row["stage5"],
                "stage6": row["stage6"],
                "attempts": int(row["attempts"]),
            }
    return players


def get_boss_data(path: Path) -> dict[str, Any]:
    """Read a bosses CSV and return a boss_data dict. Stage names are normalized to 'stageN'."""
    bosses: dict[str, Any] = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not rows:
            return bosses
        headers = {k.lower().replace(" ", "") for k in rows[0].keys()}
        _check_headers(headers, _BOSS_COLUMNS, path)
        for row in rows:
            row = _normalize(row)
            raw_stage = str(row["stage"]).lower().replace(" ", "")
            stage_key = raw_stage if raw_stage.startswith("stage") else f"stage{raw_stage}"
            bosses[stage_key] = {
                "hp": row["hp"],
                "deaths": int(row["deaths"]) if row.get("deaths") else 0,
            }
    return bosses
