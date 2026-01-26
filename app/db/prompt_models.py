"""
Database models for the new BYOK flow (Milestone 1).

This file defines how user prompts are stored in the database.
We keep it separate from older models to allow incremental development.
"""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Prompt(Base):
    """
    ORM model representing a user prompt.
    Each row = one prompt sent by a user.

    Milestone 2:
    - Store a JSON profile extracted by an LLM/stub classifier.
    """

    # Name of the table in SQLite
    __tablename__ = "prompts"

    # Primary key (auto-increment integer)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Timestamp when the prompt was stored (UTC time)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # For MVP, we identify users by username string
    # (Later this will become a foreign key to a users table or auth system)
    username: Mapped[str] = mapped_column(String, index=True)

    # The raw text of the prompt as sent by the user
    raw_prompt: Mapped[str] = mapped_column(Text)

    # ✅ Milestone 2:
    # The extracted JSON profile for this prompt.
    #
    # Example structure:
    # {
    # "task_type": "coding",
    # "needs_web": false,
    # "needs_code": true,
    # "output_format": "text",
    # "urgency": "normal",
    # "confidence": 0.75
    # }
    #
    # nullable=True because older rows (created before milestone 2) won’t have this yet.
    prompt_profile_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)