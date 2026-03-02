import pydantic_core


def get_json_data(file_name: str) -> dict:
    """Get JSON data from a file"""
    with open(f"config/{file_name}", "r") as f:
        data = f.read()
    json_data = pydantic_core.from_json(data)
    return json_data
