"""
app/db/model_catalog_repo.py
------------------------------
Milestone 3: Database-backed model catalog.

This table is the single source of truth for:
- provider model strings
- capabilities flags
- cost/latency tiers
"""

from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ModelCatalog(Base):
    """
    Each row = one available model in the router catalog.
    """

    __tablename__ = "models_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Stable identifier used in code and analytics (e.g. "gemini_flash")
    key: Mapped[str] = mapped_column(String, unique=True, index=True)

    # Provider name (e.g. "gemini", "openai")
    provider: Mapped[str] = mapped_column(String, index=True)

    # Provider-specific model name (e.g. "models/gemini-1.5-flash")
    model: Mapped[str] = mapped_column(String)

    # Tiers stored as strings for simplicity (validated at Pydantic level)
    cost_tier: Mapped[str] = mapped_column(String, default="low")       # low|medium|high
    latency_hint: Mapped[str] = mapped_column(String, default="normal") # fast|normal

    # Capabilities
    supports_web: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_json: Mapped[bool] = mapped_column(Boolean, default=True)
    good_for_code: Mapped[bool] = mapped_column(Boolean, default=True)