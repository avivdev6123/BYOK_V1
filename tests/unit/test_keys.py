"""
tests/unit/test_keys.py
-----------------------
Unit tests for encryption utility, key service, and key validation (Milestone 4).
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import User
from app.utils.encryption import encrypt_key, decrypt_key, mask_key
from app.services.key_service import (
    store_key,
    get_user_keys,
    get_decrypted_key,
    delete_key,
    build_user_keys,
    revalidate_key,
)
from app.services.key_validator import validate_key


@pytest.fixture(autouse=True)
def set_encryption_key():
    """Ensure ENCRYPTION_KEY is set for tests."""
    from cryptography.fernet import Fernet
    key = Fernet.generate_key().decode()
    os.environ["ENCRYPTION_KEY"] = key
    yield
    del os.environ["ENCRYPTION_KEY"]


MOCK_VALID = {"valid": True, "error": None, "models": ["model-1"]}
MOCK_INVALID = {"valid": False, "error": "Invalid API key", "models": []}


@pytest.fixture
def db():
    """In-memory SQLite DB with user and provider_keys tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    user = User(username="testuser", password_hash="fakehash")
    session.add(user)
    session.commit()
    session.refresh(user)
    yield session
    session.close()


# --- Encryption utility tests ---

def test_encrypt_decrypt_roundtrip():
    original = "sk-proj-abc123xyz"
    encrypted = encrypt_key(original)
    assert encrypted != original
    assert decrypt_key(encrypted) == original


def test_mask_key_long():
    assert mask_key("sk-proj-abc123xyz456") == "sk-p...z456"


def test_mask_key_short():
    assert mask_key("abcd") == "****"


# --- Key service tests (with mocked validation) ---

@patch("app.services.key_service.validate_key", return_value=MOCK_VALID)
def test_store_key_creates_record(mock_val, db):
    user = db.query(User).first()
    key = store_key(user.id, "openai", "sk-test-key-12345678", db)
    assert key.provider == "openai"
    assert key.api_key_masked == "sk-t...5678"
    assert key.api_key_encrypted is not None


@patch("app.services.key_service.validate_key", return_value=MOCK_VALID)
def test_store_key_upserts(mock_val, db):
    user = db.query(User).first()
    store_key(user.id, "openai", "sk-old-key-00000000", db)
    key = store_key(user.id, "openai", "sk-new-key-99999999", db)
    assert key.api_key_masked == "sk-n...9999"
    keys = get_user_keys(user.id, db)
    assert len(keys) == 1  # upserted, not duplicated


@patch("app.services.key_service.validate_key", return_value=MOCK_VALID)
def test_get_decrypted_key(mock_val, db):
    user = db.query(User).first()
    store_key(user.id, "gemini", "AIzaSyB-test-key", db)
    decrypted = get_decrypted_key(user.id, "gemini", db)
    assert decrypted == "AIzaSyB-test-key"


def test_get_decrypted_key_returns_none_if_missing(db):
    user = db.query(User).first()
    assert get_decrypted_key(user.id, "anthropic", db) is None


@patch("app.services.key_service.validate_key", return_value=MOCK_VALID)
def test_delete_key(mock_val, db):
    user = db.query(User).first()
    store_key(user.id, "openai", "sk-delete-me-1234", db)
    delete_key(user.id, "openai", db)
    assert get_decrypted_key(user.id, "openai", db) is None


@patch("app.services.key_service.validate_key", return_value=MOCK_VALID)
def test_build_user_keys(mock_val, db):
    user = db.query(User).first()
    store_key(user.id, "gemini", "gemini-key-123", db)
    store_key(user.id, "openai", "openai-key-456", db)
    keys = build_user_keys(user.id, db)
    assert keys == {"gemini": "gemini-key-123", "openai": "openai-key-456"}


# --- Validation status tests ---

@patch("app.services.key_service.validate_key", return_value=MOCK_VALID)
def test_store_key_sets_status_active(mock_val, db):
    user = db.query(User).first()
    key = store_key(user.id, "gemini", "AIzaSyB-real-key", db)
    assert key.status == "active"
    assert key.validated_at is not None


@patch("app.services.key_service.validate_key", return_value=MOCK_INVALID)
def test_store_key_sets_status_invalid(mock_val, db):
    user = db.query(User).first()
    key = store_key(user.id, "gemini", "bad-key-123", db)
    assert key.status == "invalid"
    assert key.validated_at is not None


@patch("app.services.key_service.validate_key", return_value=MOCK_VALID)
def test_revalidate_key_updates_status(mock_val, db):
    user = db.query(User).first()
    # Store as invalid first
    with patch("app.services.key_service.validate_key", return_value=MOCK_INVALID):
        store_key(user.id, "openai", "sk-real-key-12345678", db)
    keys = get_user_keys(user.id, db)
    assert keys[0].status == "invalid"

    # Revalidate — now it's valid
    updated = revalidate_key(user.id, "openai", db)
    assert updated.status == "active"


def test_revalidate_key_returns_none_if_missing(db):
    user = db.query(User).first()
    assert revalidate_key(user.id, "openai", db) is None


# --- Key validator unit tests (mocked SDKs) ---

@patch("app.services.key_validator.genai")
def test_validate_gemini_valid(mock_genai):
    mock_model = MagicMock()
    mock_model.name = "models/gemini-1.5-flash"
    mock_client = MagicMock()
    mock_client.models.list.return_value = [mock_model]
    mock_genai.Client.return_value = mock_client

    result = validate_key("gemini", "AIzaSyB-test")
    assert result["valid"] is True
    assert "models/gemini-1.5-flash" in result["models"]


@patch("app.services.key_validator.OpenAI")
def test_validate_openai_valid(mock_openai_cls):
    mock_model = MagicMock()
    mock_model.id = "gpt-4o"
    mock_response = MagicMock()
    mock_response.data = [mock_model]
    mock_client = MagicMock()
    mock_client.models.list.return_value = mock_response
    mock_openai_cls.return_value = mock_client

    result = validate_key("openai", "sk-test")
    assert result["valid"] is True
    assert "gpt-4o" in result["models"]


@patch("app.services.key_validator.Anthropic")
def test_validate_anthropic_valid(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    result = validate_key("anthropic", "sk-ant-test")
    assert result["valid"] is True
    assert len(result["models"]) > 0


@patch("app.services.key_validator.genai")
def test_validate_gemini_invalid(mock_genai):
    mock_genai.Client.side_effect = Exception("Invalid API key")

    result = validate_key("gemini", "bad-key")
    assert result["valid"] is False
    assert "Invalid API key" in result["error"]


@patch("app.services.key_validator.OpenAI")
def test_validate_openai_invalid(mock_openai_cls):
    mock_client = MagicMock()
    mock_client.models.list.side_effect = Exception("Incorrect API key")
    mock_openai_cls.return_value = mock_client

    result = validate_key("openai", "bad-key")
    assert result["valid"] is False
    assert "Incorrect API key" in result["error"]


def test_validate_unknown_provider():
    result = validate_key("unknown", "some-key")
    assert result["valid"] is False
    assert "Unknown provider" in result["error"]