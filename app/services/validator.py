import json

def validate_json(text: str) -> None:
    json.loads(text)
