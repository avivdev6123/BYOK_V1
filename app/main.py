from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes_generate import router as generate_router
from app.api.v1.routes_usage import router as usage_router
from app.api.v1.routes_prompts import router as prompts_router
from app.api.v1.routes_route_to_model import router as routing_router
from app.api.v1.routes_completion import router as completion_router

from app.db.session import engine
from app.db.base import Base
from app.db import models, prompt_models, model_catalog_models  # noqa: F401


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BYOK LLM Router",
    version="0.1.0",
    description="BYOK (Bring Your Own Key) routing, cost control, policies, and fallback for LLM providers.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


##@app.get("/health")
#async def health():
#    return {"status": "ok"}

app.include_router(generate_router, prefix="/v1", tags=["generate"])
app.include_router(usage_router, prefix="/v1", tags=["usage"])
app.include_router(prompts_router, prefix="/v1", tags=["prompts"])
app.include_router(routing_router, prefix="/v1", tags=["model_routing"])
app.include_router(completion_router, prefix="/v1", tags=["completions"])