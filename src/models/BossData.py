from typing import Any, Self

from pydantic import BaseModel, RootModel, field_validator


class BossData(BaseModel):
    """Data Model for a single boss stage"""

    hp: float
    deaths: int

    @field_validator("hp", mode="before")
    def convert_percentages(cls, hp: Any) -> Self:
        """Validates the data model and converts percentages to floats in case they are present"""

        if type(hp) is str and hp.endswith("%"):
            hp = float(hp[:-1])
        return hp


class BossesData(RootModel):
    """Data model for all boss stages"""

    root: dict[str, BossData]
