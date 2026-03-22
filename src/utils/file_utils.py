from pathlib import Path
from typing import Any

import pydantic_core


def get_json_data(path: Path) -> dict[str, Any]:
    """Read and parse a JSON file, returning its contents as a dict."""
    result: dict[str, Any] = pydantic_core.from_json(path.read_text(encoding="utf-8"))
    return result
