"""
app/services/key_service.py
---------------------------
Milestone 4: Per-user API key management.

Handles storing, retrieving, and deleting encrypted provider API keys.
Validates keys on save via real provider API calls.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import ProviderKey
from app.utils.encryption import encrypt_key, decrypt_key, mask_key
from app.services.key_validator import validate_key


def store_key(user_id: int, provider: str, api_key: str, db: Session) -> ProviderKey:
    """Encrypt, validate, and store (or update) a provider key for a user."""
    existing = db.query(ProviderKey).filter(
        ProviderKey.user_id == user_id,
        ProviderKey.provider == provider,
    ).first()
    encrypted = encrypt_key(api_key)
    masked = mask_key(api_key)

    # Validate the key against the provider API
    result = validate_key(provider, api_key)
    status = "active" if result["valid"] else "invalid"
    now = datetime.utcnow()

    models = result.get("models", [])

    if existing:
        existing.api_key_encrypted = encrypted
        existing.api_key_masked = masked
        existing.status = status
        existing.validated_at = now
        existing.discovered_models = models
    else:
        existing = ProviderKey(
            user_id=user_id,
            provider=provider,
            api_key_encrypted=encrypted,
            api_key_masked=masked,
            status=status,
            validated_at=now,
            discovered_models=models,
        )
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing


def revalidate_key(user_id: int, provider: str, db: Session) -> ProviderKey | None:
    """Re-validate an existing stored key and update its status."""
    row = db.query(ProviderKey).filter(
        ProviderKey.user_id == user_id,
        ProviderKey.provider == provider,
    ).first()
    if not row or not row.api_key_encrypted:
        return None

    api_key = decrypt_key(row.api_key_encrypted)
    result = validate_key(provider, api_key)
    row.status = "active" if result["valid"] else "invalid"
    row.validated_at = datetime.utcnow()
    row.discovered_models = result.get("models", [])
    db.commit()
    db.refresh(row)
    return row


def get_user_keys(user_id: int, db: Session) -> list[ProviderKey]:
    """List all provider keys for a user (masked, not decrypted)."""
    return db.query(ProviderKey).filter(ProviderKey.user_id == user_id).all()


def get_decrypted_key(user_id: int, provider: str, db: Session) -> str | None:
    """Return decrypted API key for a specific provider, or None if not set."""
    row = db.query(ProviderKey).filter(
        ProviderKey.user_id == user_id,
        ProviderKey.provider == provider,
    ).first()
    if not row or not row.api_key_encrypted:
        return None
    return decrypt_key(row.api_key_encrypted)


def delete_key(user_id: int, provider: str, db: Session) -> None:
    """Remove a stored key."""
    db.query(ProviderKey).filter(
        ProviderKey.user_id == user_id,
        ProviderKey.provider == provider,
    ).delete()
    db.commit()


def build_user_keys(user_id: int, db: Session) -> dict[str, str]:
    """Load all decrypted keys for a user as a dict (provider -> key)."""
    rows = db.query(ProviderKey).filter(ProviderKey.user_id == user_id).all()
    result = {}
    for row in rows:
        if row.api_key_encrypted:
            result[row.provider] = decrypt_key(row.api_key_encrypted)
    return result