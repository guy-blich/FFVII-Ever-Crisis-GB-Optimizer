"""Tests for sheets_utils using a mocked gspread client."""

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


def _make_mock_gspread() -> ModuleType:
    """Return a minimal gspread stub so tests run without the real package."""
    mock = ModuleType("gspread")
    mock.service_account = MagicMock()
    return mock


def _make_sheet(players_rows: list[dict], bosses_rows: list[dict]) -> MagicMock:
    """Build a mock gspread Spreadsheet with Players and Bosses worksheets."""
    players_ws = MagicMock()
    players_ws.get_all_records.return_value = players_rows

    bosses_ws = MagicMock()
    bosses_ws.get_all_records.return_value = bosses_rows

    sheet = MagicMock()
    sheet.worksheet.side_effect = lambda name: (players_ws if name == "Players" else bosses_ws)
    return sheet


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_PLAYERS = [
    {
        "player": "Alice",
        "stage1": 100.0,
        "stage2": 90.0,
        "stage3": 70.0,
        "stage4": 40.0,
        "stage5": 20.0,
        "stage6": 10.0,
        "attempts": 3,
    },
    {
        "player": "Bob",
        "stage1": "80%",
        "stage2": "60%",
        "stage3": "45%",
        "stage4": "25%",
        "stage5": "12%",
        "stage6": "6%",
        "attempts": 2,
    },
]

_SAMPLE_BOSSES = [
    {"stage": "stage1", "hp": "100%", "deaths": 0},
    {"stage": "Stage 2", "hp": 75.0, "deaths": 1},
    {"stage": "stage3", "hp": "100%", "deaths": 0},
    {"stage": "stage4", "hp": "100%", "deaths": 0},
    {"stage": "stage5", "hp": "100%", "deaths": 0},
    {"stage": "stage6", "hp": "100%", "deaths": 0},
]


@pytest.fixture(autouse=True)
def _stub_gspread(monkeypatch):
    """Inject a fake gspread module for every test in this file."""
    fake = _make_mock_gspread()
    monkeypatch.setitem(sys.modules, "gspread", fake)
    # Also remove cached import inside sheets_utils if already imported
    import importlib
    import src.utils.sheets_utils as su

    importlib.reload(su)
    yield fake


# ---------------------------------------------------------------------------
# get_player_data
# ---------------------------------------------------------------------------


class TestGetPlayerData:
    def test_returns_all_players(self):
        from src.utils.sheets_utils import get_player_data

        sheet = _make_sheet(_SAMPLE_PLAYERS, [])
        result = get_player_data(sheet, "Players")
        assert set(result.keys()) == {"Alice", "Bob"}

    def test_numeric_scores_preserved(self):
        from src.utils.sheets_utils import get_player_data

        sheet = _make_sheet(_SAMPLE_PLAYERS, [])
        result = get_player_data(sheet, "Players")
        assert result["Alice"]["stage1"] == 100.0
        assert result["Alice"]["attempts"] == 3

    def test_percentage_strings_passed_through(self):
        """Percentage strings are forwarded as-is; Pydantic validators strip the %."""
        from src.utils.sheets_utils import get_player_data

        sheet = _make_sheet(_SAMPLE_PLAYERS, [])
        result = get_player_data(sheet, "Players")
        assert result["Bob"]["stage1"] == "80%"

    def test_skips_blank_player_names(self):
        from src.utils.sheets_utils import get_player_data

        rows = [
            {
                "player": "",
                "stage1": 50.0,
                "stage2": 50.0,
                "stage3": 50.0,
                "stage4": 50.0,
                "stage5": 50.0,
                "stage6": 50.0,
                "attempts": 1,
            }
        ]
        sheet = _make_sheet(rows, [])
        result = get_player_data(sheet, "Players")
        assert result == {}

    def test_column_headers_are_case_insensitive(self):
        from src.utils.sheets_utils import get_player_data

        rows = [
            {
                "Player": "Carol",
                "Stage1": 55.0,
                "Stage2": 45.0,
                "Stage3": 35.0,
                "Stage4": 25.0,
                "Stage5": 15.0,
                "Stage6": 5.0,
                "Attempts": 1,
            }
        ]
        sheet = _make_sheet(rows, [])
        result = get_player_data(sheet, "Players")
        assert "Carol" in result
        assert result["Carol"]["stage1"] == 55.0


# ---------------------------------------------------------------------------
# get_boss_data
# ---------------------------------------------------------------------------


class TestGetBossData:
    def test_returns_all_stages(self):
        from src.utils.sheets_utils import get_boss_data

        sheet = _make_sheet([], _SAMPLE_BOSSES)
        result = get_boss_data(sheet, "Bosses")
        assert set(result.keys()) == {f"stage{i}" for i in range(1, 7)}

    def test_normalizes_stage_name_with_space(self):
        """'Stage 2' should be stored as 'stage2'."""
        from src.utils.sheets_utils import get_boss_data

        sheet = _make_sheet([], _SAMPLE_BOSSES)
        result = get_boss_data(sheet, "Bosses")
        assert "stage2" in result
        assert result["stage2"]["hp"] == 75.0

    def test_numeric_stage_key_normalized(self):
        """A bare '3' in the stage column becomes 'stage3'."""
        from src.utils.sheets_utils import get_boss_data

        rows = [{"stage": "3", "hp": "50%", "deaths": 0}]
        sheet = _make_sheet([], rows)
        result = get_boss_data(sheet, "Bosses")
        assert "stage3" in result

    def test_deaths_defaults_to_zero(self):
        from src.utils.sheets_utils import get_boss_data

        rows = [{"stage": "stage1", "hp": 100.0}]  # no deaths column
        sheet = _make_sheet([], rows)
        result = get_boss_data(sheet, "Bosses")
        assert result["stage1"]["deaths"] == 0


# ---------------------------------------------------------------------------
# open_sheet
# ---------------------------------------------------------------------------


class TestOpenSheet:
    def test_calls_service_account_with_credentials(self, _stub_gspread):
        from src.utils.sheets_utils import open_sheet

        open_sheet("SHEET_ID", Path("creds.json"))
        _stub_gspread.service_account.assert_called_once_with(filename="creds.json")

    def test_opens_sheet_by_key(self, _stub_gspread):
        from src.utils.sheets_utils import open_sheet

        mock_client = _stub_gspread.service_account.return_value
        open_sheet("MY_SHEET_ID", Path("creds.json"))
        mock_client.open_by_key.assert_called_once_with("MY_SHEET_ID")


# ---------------------------------------------------------------------------
# Missing gspread
# ---------------------------------------------------------------------------


class TestMissingGspread:
    def test_import_error_raised_without_gspread(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "gspread", None)
        import importlib
        import src.utils.sheets_utils as su

        importlib.reload(su)
        with pytest.raises(ImportError, match="gspread is required"):
            su._require_gspread()
