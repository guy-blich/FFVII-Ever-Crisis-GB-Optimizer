from typing import Any, Self

from pydantic import BaseModel, RootModel


class PlayerData(BaseModel):
    """Data model for a single player/guild member"""

    stage1: float
    stage2: float
    stage3: float
    stage4: float
    stage5: float
    attempts: int

    @classmethod
    def model_validate(cls, obj: Any, *args, **kwargs) -> Self:
        """Validates the data model and converts percentages to floats in case they are present"""

        for key, value in obj.items():
            if key.startswith("stage"):
                if type(value) is str and value.endswith("%"):
                    obj[key] = float(value[:-1])
        return super().model_validate(obj)


class PlayersData(RootModel):
    """Data model for all players/guild members"""

    root: dict[str, PlayerData]
