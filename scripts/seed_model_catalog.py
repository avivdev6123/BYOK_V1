"""
scripts/seed_model_catalog.py
-----------------------------
Populate models_catalog with default entries.

Run:
python scripts/seed_model_catalog.py
"""

from app.db.session import SessionLocal
from app.db.model_catalog_models import ModelCatalog


DEFAULT_MODELS = [
    ModelCatalog(
        key="gemini_flash",
        provider="gemini",
        model="models/gemini-2.5-flash",
        cost_tier="low",
        latency_hint="fast",
        supports_web=False,
        supports_json=True,
        good_for_code=True,
    ),
    ModelCatalog(
        key="gemini_pro",
        provider="gemini",
        model="models/gemini-1.5-pro",
        cost_tier="medium",
        latency_hint="normal",
        supports_web=False,
        supports_json=True,
        good_for_code=True,
    ),
    ModelCatalog(
        key="openai_mini",
        provider="openai",
        model="gpt-4o-mini",
        cost_tier="low",
        latency_hint="fast",
        supports_web=False,
        supports_json=True,
        good_for_code=True,
    ),
]


def main() -> None:
    db = SessionLocal()
    try:
        for m in DEFAULT_MODELS:
            exists = db.query(ModelCatalog).filter(ModelCatalog.key == m.key).first()
            if not exists:
                db.add(m)
        db.commit()
        print("✅ Seeded models_catalog")
    finally:
        db.close()


if __name__ == "__main__":
    main()