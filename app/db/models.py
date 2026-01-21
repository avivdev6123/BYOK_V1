from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)

    budgets = relationship("Budget", back_populates="user")
    requests = relationship("RequestLog", back_populates="user")

class Budget(Base):
    __tablename__ = "budgets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    monthly_budget_usd: Mapped[float] = mapped_column(Float, default=20.0)
    spent_usd: Mapped[float] = mapped_column(Float, default=0.0)

    user = relationship("User", back_populates="budgets")

class RequestLog(Base):
    __tablename__ = "request_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    prompt: Mapped[str] = mapped_column(Text)
    require_json: Mapped[bool] = mapped_column(Boolean, default=False)

    chosen_provider: Mapped[str] = mapped_column(String)
    chosen_model: Mapped[str] = mapped_column(String)

    input_tokens_est: Mapped[int] = mapped_column(Integer)
    output_tokens_est: Mapped[int] = mapped_column(Integer)

    estimated_cost_usd: Mapped[float] = mapped_column(Float)
    attempts: Mapped[int] = mapped_column(Integer)

    user = relationship("User", back_populates="requests")

class ProviderKey(Base):
    """
    MVP: store keys later (encrypted). For now keep structure.
    """
    __tablename__ = "provider_keys"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String, index=True)
    api_key_masked: Mapped[str] = mapped_column(String)  # store masked (e.g. sk-***abcd)

class ModelCatalog(Base):
    __tablename__ = "model_catalog"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String, index=True)
    model: Mapped[str] = mapped_column(String, index=True)
    supports_json: Mapped[bool] = mapped_column(Boolean, default=True)
    latency: Mapped[str] = mapped_column(String, default="standard")
    context_tokens: Mapped[int] = mapped_column(Integer, default=128000)

    # Pricing stored here for simplicity (MVP)
    in_per_1m: Mapped[float] = mapped_column(Float)
    out_per_1m: Mapped[float] = mapped_column(Float)
