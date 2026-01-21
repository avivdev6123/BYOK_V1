from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models import RequestLog, User, Budget

router = APIRouter()

@router.get("/usage")
def usage(username: str = "demo", db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return {"error": "user not found"}

    total_cost = (
        db.query(func.sum(RequestLog.estimated_cost_usd))
        .filter(RequestLog.user_id == user.id)
        .scalar()
        or 0.0
    )

    total_requests = (
        db.query(func.count(RequestLog.id))
        .filter(RequestLog.user_id == user.id)
        .scalar()
        or 0
    )

    budget = db.query(Budget).filter(Budget.user_id == user.id).first()
    remaining = None
    if budget:
        remaining = round(budget.monthly_budget_usd - budget.spent_usd, 6)

    last_requests = (
        db.query(RequestLog)
        .filter(RequestLog.user_id == user.id)
        .order_by(RequestLog.id.desc())
        .limit(10)
        .all()
    )

    return {
        "username": username,
        "total_requests": int(total_requests),
        "total_estimated_cost_usd": round(float(total_cost), 8),
        "budget_remaining_usd": remaining,
        "last_10": [
            {
                "id": r.id,
                "provider": r.chosen_provider,
                "model": r.chosen_model,
                "estimated_cost_usd": r.estimated_cost_usd,
                "attempts": r.attempts,
                "created_at": r.created_at.isoformat(),
            }
            for r in last_requests
        ],
    }
