from typing import Any

from pydantic import BaseModel, RootModel, field_validator


class BossData(BaseModel):
    """Data model for a single boss stage."""

    hp: float
    deaths: int

    @field_validator("hp", mode="before")
    @classmethod
    def convert_percentage(cls, hp: Any) -> float:
        """Strips a trailing '%' and converts the value to float."""
        if isinstance(hp, str) and hp.endswith("%"):
            return float(hp[:-1])
        return hp


class BossesData(RootModel):
    """Data model for all boss stages"""

    root: dict[str, BossData]
