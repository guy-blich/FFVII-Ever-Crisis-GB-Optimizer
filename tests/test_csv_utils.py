"""Tests for csv_utils using temporary CSV files."""

import textwrap
from pathlib import Path

import pytest

from src.utils.csv_utils import get_player_data, get_boss_data


@pytest.fixture
def tmp_players(tmp_path: Path) -> Path:
    p = tmp_path / "players.csv"
    p.write_text(
        textwrap.dedent(
            """\
        player,stage1,stage2,stage3,stage4,stage5,stage6,attempts
        Alice,100,90,70,40,20,10,3
        Bob,80%,60%,45%,25%,12%,6%,2
    """
        )
    )
    return p


@pytest.fixture
def tmp_bosses(tmp_path: Path) -> Path:
    p = tmp_path / "bosses.csv"
    p.write_text(
        textwrap.dedent(
            """\
        stage,hp,deaths
        stage1,100%,0
        Stage 2,75%,1
        3,100%,0
        stage4,100%,0
        stage5,100%,0
        stage6,100%,0
    """
        )
    )
    return p


class TestGetPlayerData:
    def test_returns_all_players(self, tmp_players: Path) -> None:
        result = get_player_data(tmp_players)
        assert set(result.keys()) == {"Alice", "Bob"}

    def test_numeric_scores_preserved(self, tmp_players: Path) -> None:
        result = get_player_data(tmp_players)
        assert result["Alice"]["stage1"] == "100"
        assert result["Alice"]["attempts"] == 3

    def test_percentage_strings_passed_through(self, tmp_players: Path) -> None:
        result = get_player_data(tmp_players)
        assert result["Bob"]["stage1"] == "80%"

    def test_skips_blank_player_names(self, tmp_path: Path) -> None:
        p = tmp_path / "players.csv"
        p.write_text(
            "player,stage1,stage2,stage3,stage4,stage5,stage6,attempts\n" ",50,50,50,50,50,50,1\n"
        )
        assert get_player_data(p) == {}

    def test_case_insensitive_headers(self, tmp_path: Path) -> None:
        p = tmp_path / "players.csv"
        p.write_text(
            "Player,Stage1,Stage2,Stage3,Stage4,Stage5,Stage6,Attempts\n"
            "Carol,55,45,35,25,15,5,1\n"
        )
        result = get_player_data(p)
        assert "Carol" in result
        assert result["Carol"]["stage1"] == "55"


class TestGetBossData:
    def test_returns_all_stages(self, tmp_bosses: Path) -> None:
        result = get_boss_data(tmp_bosses)
        assert set(result.keys()) == {f"stage{i}" for i in range(1, 7)}

    def test_normalizes_stage_name_with_space(self, tmp_bosses: Path) -> None:
        result = get_boss_data(tmp_bosses)
        assert "stage2" in result
        assert result["stage2"]["hp"] == "75%"

    def test_numeric_stage_key_normalized(self, tmp_bosses: Path) -> None:
        result = get_boss_data(tmp_bosses)
        assert "stage3" in result

    def test_deaths_parsed_correctly(self, tmp_bosses: Path) -> None:
        result = get_boss_data(tmp_bosses)
        assert result["stage2"]["deaths"] == 1

    def test_deaths_defaults_to_zero(self, tmp_path: Path) -> None:
        p = tmp_path / "bosses.csv"
        p.write_text("stage,hp\nstage1,100%\n")
        result = get_boss_data(p)
        assert result["stage1"]["deaths"] == 0
