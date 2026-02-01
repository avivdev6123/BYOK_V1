from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.routing import RouteRequest, RouteResponse
from app.services.model_catalog_repo import load_catalog
from app.services.model_selector import ModelSelector
from app.services.deterministic_router import DeterministicRouter

router = APIRouter()


@router.post("/route", response_model=RouteResponse)
def route_prompt(req: RouteRequest, db: Session = Depends(get_db)) -> RouteResponse:
    # 1) Load models from DB
    catalog = load_catalog(db)

    if not catalog:
        raise HTTPException(status_code=500, detail="Model catalog is empty. Seed models_catalog table.")

    # 2) Build router engine
    selector = ModelSelector(catalog=catalog)
    router_engine = DeterministicRouter(selector=selector)

    # 3) Route
    decision = router_engine.route(req.profile)

    if decision.selected is None:
        raise HTTPException(status_code=422, detail=decision.reason)

    return RouteResponse(decision=decision)