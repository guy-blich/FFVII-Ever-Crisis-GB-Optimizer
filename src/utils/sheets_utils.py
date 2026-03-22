"""Google Sheets data source.

Requires the 'sheets' optional dependency:
    pip install gspread>=6.0

Authentication uses a Google service account. See README for setup instructions.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import gspread


def _require_gspread() -> "gspread":
    try:
        import gspread

        return gspread
    except ImportError:
        raise ImportError(
            "gspread is required for Google Sheets support.\n"
            "Install it with:  pip install gspread>=6.0\n"
            "Or:               pip install -r requirements-sheets.txt"
        )


def open_sheet(sheet_id: str, credentials_path: Path) -> "gspread.Spreadsheet":
    """Open a Google Sheet by ID using a service account credentials file."""
    gspread = _require_gspread()
    client = gspread.service_account(filename=str(credentials_path))
    return client.open_by_key(sheet_id)


def get_player_data(sheet: "gspread.Spreadsheet", tab_name: str) -> dict:
    """Read the Players tab and return a player_data dict. Headers are case-insensitive."""
    records = sheet.worksheet(tab_name).get_all_records()
    players: dict = {}
    for row in records:
        row = {k.lower().replace(" ", ""): v for k, v in row.items()}
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


def get_boss_data(sheet: "gspread.Spreadsheet", tab_name: str) -> dict:
    """Read the Bosses tab and return a boss_data dict. Stage names are normalized to 'stageN'."""
    records = sheet.worksheet(tab_name).get_all_records()
    bosses: dict = {}
    for row in records:
        row = {k.lower().replace(" ", ""): v for k, v in row.items()}
        # Normalize "Stage 1" / "stage 1" / "1" → "stage1"
        raw_stage = str(row["stage"]).lower().replace(" ", "")
        stage_key = raw_stage if raw_stage.startswith("stage") else f"stage{raw_stage}"
        bosses[stage_key] = {
            "hp": row["hp"],
            "deaths": int(row.get("deaths", 0)),
        }
    return bosses
