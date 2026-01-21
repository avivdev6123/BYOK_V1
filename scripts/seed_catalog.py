from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.db import models  # noqa: F401  ensures models are registered
from app.db.models import User, Budget, ModelCatalog

def seed():
    # ✅ Ensure tables exist even when FastAPI server is not running
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    user = db.query(User).filter(User.username == "demo").first()
    if not user:
        user = User(username="demo")
        db.add(user)
        db.commit()
        db.refresh(user)

    budget = db.query(Budget).filter(Budget.user_id == user.id).first()
    if not budget:
        db.add(Budget(user_id=user.id, monthly_budget_usd=5.0, spent_usd=0.0))
        db.commit()

    models_to_seed = [
        ModelCatalog(provider="openai", model="gpt-4o-mini", supports_json=True, latency="fast",
                     context_tokens=128000, in_per_1m=0.05, out_per_1m=0.15),
        ModelCatalog(provider="google", model="gemini-1.5-flash", supports_json=True, latency="fast",
                     context_tokens=128000, in_per_1m=0.10, out_per_1m=0.40),
        ModelCatalog(provider="openai", model="gpt-4o", supports_json=True, latency="standard",
                     context_tokens=128000, in_per_1m=5.0, out_per_1m=15.0),
    ]

    for m in models_to_seed:
        exists = (
            db.query(ModelCatalog)
            .filter(ModelCatalog.provider == m.provider, ModelCatalog.model == m.model)
            .first()
        )
        if not exists:
            db.add(m)

    db.commit()
    db.close()
    print("Seed complete. User=demo")

if __name__ == "__main__":
    seed()
