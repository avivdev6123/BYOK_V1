import pytest
from app.services.validator import validate_json

def test_validate_json_ok():
    validate_json('{"ok": true}')

def test_validate_json_fail():
    with pytest.raises(Exception):
        validate_json("{bad json}")
