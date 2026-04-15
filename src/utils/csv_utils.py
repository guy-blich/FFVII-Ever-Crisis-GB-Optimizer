import csv
from pathlib import Path
from typing import Any

_PLAYER_COLUMNS = {"player", "stage1", "stage2", "stage3", "stage4", "stage5", "stage6", "attempts"}
_BOSS_COLUMNS = {"stage", "hp"}

# Column indices for the raw spreadsheet export format.
_COL_NAME = 0
_COL_STAGES = slice(3, 9)  # Stage 1–6 under "Average Mock Scores"
_COL_AVAIL = slice(16, 25)  # 9 TRUE/FALSE availability slots


def _normalize(row: Any) -> dict[str, Any]:
    return {k.lower().replace(" ", ""): v for k, v in row.items()}


def _check_headers(found: set[str], required: set[str], path: Path) -> None:
    missing = required - found
    if missing:
        raise SystemExit(
            f"error: {path} is missing required columns: {', '.join(sorted(missing))}\n"
            f"  Found: {', '.join(sorted(found))}"
        )


def _is_sheet_export(path: Path) -> bool:
    """Return True if this looks like a raw guild spreadsheet export (multi-header rows)."""
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        second = next(reader, [])
    return bool(second) and second[0].lower().replace(" ", "") == "playername"


def _clean_score(value: str) -> str:
    """Return a usable score string, defaulting to '0%' for blank or error cells."""
    v = value.strip()
    return v if (v and v != "#REF!") else "0%"


def _parse_sheet_export_players(path: Path) -> dict[str, Any]:
    """Parse the raw guild spreadsheet export into a player_data dict."""
    players: dict[str, Any] = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # metadata row
        next(reader)  # header row (we use column positions)
        next(reader)  # notes row
        for row in reader:
            if len(row) <= _COL_NAME:
                continue
            name = row[_COL_NAME].strip()
            if not name:
                continue

            stage_cols = row[_COL_STAGES]
            # Skip players with no scores entered
            if all(v.strip() in ("", "#REF!") for v in stage_cols):
                continue

            avail_cols = row[_COL_AVAIL] if len(row) > _COL_AVAIL.start else []
            attempts = sum(1 for v in avail_cols if v.strip().upper() == "TRUE")
            if attempts == 0:
                continue

            players[name] = {
                "stage1": _clean_score(stage_cols[0]),
                "stage2": _clean_score(stage_cols[1]),
                "stage3": _clean_score(stage_cols[2]),
                "stage4": _clean_score(stage_cols[3]),
                "stage5": _clean_score(stage_cols[4]) if len(stage_cols) > 4 else "0%",
                "stage6": _clean_score(stage_cols[5]) if len(stage_cols) > 5 else "0%",
                "attempts": attempts,
            }
    return players


def get_player_data(path: Path) -> dict[str, Any]:
    """Read a players CSV and return a player_data dict. Headers are case-insensitive.

    Also accepts raw guild spreadsheet exports (multi-header format), detected automatically.
    """
    if _is_sheet_export(path):
        return _parse_sheet_export_players(path)

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
