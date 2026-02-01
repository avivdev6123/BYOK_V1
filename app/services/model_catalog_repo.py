"""
app/services/model_catalog_repo.py
----------------------------------
Milestone 3: Load model catalog entries from the database.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.model_catalog_models import ModelCatalog


def load_catalog(db: Session) -> list[ModelCatalog]:
    """
    Load enabled catalog models from DB.
    Returns ORM rows (ModelCatalog).
    """
    return db.query(ModelCatalog).order_by(ModelCatalog.id.asc()).all()
