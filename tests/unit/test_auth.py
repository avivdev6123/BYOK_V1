"""
tests/unit/test_auth.py
-----------------------
Unit tests for the auth service (Milestone 4).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.services.auth_service import (
    register_user,
    login_user,
    get_user_from_token,
    logout,
    _sessions,
)


@pytest.fixture
def db():
    """In-memory SQLite DB with user table."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    _sessions.clear()


def test_register_creates_user(db):
    user = register_user("alice", "secret123", db)
    assert user.id is not None
    assert user.username == "alice"
    assert user.password_hash is not None
    assert user.password_hash != "secret123"  # must be hashed


def test_register_duplicate_raises(db):
    register_user("alice", "secret123", db)
    with pytest.raises(ValueError, match="already exists"):
        register_user("alice", "other456", db)


def test_login_valid_credentials(db):
    register_user("alice", "secret123", db)
    user, token = login_user("alice", "secret123", db)
    assert user.username == "alice"
    assert len(token) > 0


def test_login_wrong_password(db):
    register_user("alice", "secret123", db)
    with pytest.raises(ValueError, match="Invalid password"):
        login_user("alice", "wrongpass", db)


def test_login_nonexistent_user(db):
    with pytest.raises(LookupError, match="User not found"):
        login_user("ghost", "secret123", db)


def test_get_user_from_valid_token(db):
    register_user("alice", "secret123", db)
    _, token = login_user("alice", "secret123", db)
    user = get_user_from_token(token, db)
    assert user.username == "alice"


def test_get_user_from_invalid_token(db):
    with pytest.raises(LookupError, match="Invalid or expired"):
        get_user_from_token("fake-token", db)


def test_logout_invalidates_token(db):
    register_user("alice", "secret123", db)
    _, token = login_user("alice", "secret123", db)
    logout(token)
    with pytest.raises(LookupError, match="Invalid or expired"):
        get_user_from_token(token, db)