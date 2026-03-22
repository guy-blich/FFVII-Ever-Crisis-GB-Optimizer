from typing import Any

from pydantic import BaseModel, RootModel, field_validator


class PlayerData(BaseModel):
    """Data model for a single player/guild member."""

    stage1: float
    stage2: float
    stage3: float
    stage4: float
    stage5: float
    stage6: float
    attempts: int

    @field_validator("stage1", "stage2", "stage3", "stage4", "stage5", "stage6", mode="before")
    @classmethod
    def convert_percentage(cls, value: Any) -> float:
        if isinstance(value, str) and value.endswith("%"):
            return float(value[:-1])
        return value


class PlayersData(RootModel):
    """Data model for all players/guild members."""

    root: dict[str, PlayerData]
