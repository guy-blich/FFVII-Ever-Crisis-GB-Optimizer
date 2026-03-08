from pathlib import Path

import pydantic_core


def get_json_data(path: Path) -> dict:
    """Read and parse a JSON file, returning its contents as a dict."""
    return pydantic_core.from_json(path.read_text(encoding="utf-8"))
