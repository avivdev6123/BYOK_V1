from fastapi import APIRouter, HTTPException
from app.schemas.generate import GenerateRequest, GenerateResponse
from app.services.router import route_and_generate

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    try:
        return await route_and_generate(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
