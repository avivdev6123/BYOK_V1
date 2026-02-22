"""
app/utils/encryption.py
-----------------------
Milestone 4: Fernet symmetric encryption for API key storage.

Requires ENCRYPTION_KEY env var (a Fernet key).
Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

import os

from cryptography.fernet import Fernet


def _get_fernet() -> Fernet:
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise RuntimeError(
            "Missing ENCRYPTION_KEY env var. Generate with: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode())


def encrypt_key(plaintext: str) -> str:
    """Encrypt a plaintext API key."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_key(ciphertext: str) -> str:
    """Decrypt an encrypted API key."""
    return _get_fernet().decrypt(ciphertext.encode()).decode()


def mask_key(plaintext: str) -> str:
    """Mask a key for display: sk-ab...wxyz"""
    if len(plaintext) <= 8:
        return "****"
    return plaintext[:4] + "..." + plaintext[-4:]