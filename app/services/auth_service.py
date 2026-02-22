"""
app/services/auth_service.py
-----------------------------
Milestone 4: Authentication business logic.

In-memory session store for MVP. Replace with DB-backed sessions or JWT later.
"""

import secrets

import bcrypt
from sqlalchemy.orm import Session

from app.db.models import User

# In-memory session store: token -> user_id
# Swap for Redis or DB table for production.
_sessions: dict[str, int] = {}


def register_user(username: str, password: str, db: Session) -> User:
    """Create a new user with bcrypt-hashed password."""
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise ValueError(f"Username '{username}' already exists")
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(username=username, password_hash=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(username: str, password: str, db: Session) -> tuple[User, str]:
    """Verify credentials and create a session token."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise LookupError("User not found")
    if not user.password_hash:
        raise ValueError("Account has no password set")
    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        raise ValueError("Invalid password")
    token = secrets.token_urlsafe(32)
    _sessions[token] = user.id
    return user, token


def get_user_from_token(token: str, db: Session) -> User:
    """Resolve a session token to a User."""
    user_id = _sessions.get(token)
    if user_id is None:
        raise LookupError("Invalid or expired session")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise LookupError("User not found for session")
    return user


def logout(token: str) -> None:
    """Invalidate a session token."""
    _sessions.pop(token, None)