"""
app/services/completion_service.py
----------------------------------
Milestone 3B: Completion orchestrator.

Pipeline: load prompt -> route -> execute LLM (with fallback) -> return response.
"""

from sqlalchemy.orm import Session

from app.db.prompt_models import Prompt
from app.schemas.prompts import PromptProfile
from app.schemas.completion import CompletionResponse, WebSource
from app.services.model_catalog_repo import load_catalog
from app.services.model_selector import ModelSelector
from app.services.deterministic_router import DeterministicRouter
from app.services.LLM_completion import LLMCompletionClient

MAX_FALLBACK_ATTEMPTS = 3


def execute_completion(prompt_id: int, db: Session, client: LLMCompletionClient) -> CompletionResponse:
    """
    Full completion pipeline:
    1. Load prompt from DB
    2. Route using stored profile
    3. Execute LLM call with fallback
    """

    # 1) Load prompt
    row = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not row:
        raise LookupError(f"Prompt {prompt_id} not found")

    if not row.prompt_profile_json:
        raise ValueError(f"Prompt {prompt_id} has no profile — run profiling first")

    profile = PromptProfile(**row.prompt_profile_json)

    # 2) Route
    catalog = load_catalog(db)
    if not catalog:
        raise RuntimeError("Model catalog is empty. Seed models_catalog table.")

    selector = ModelSelector(catalog=catalog)
    router = DeterministicRouter(selector=selector)
    decision = router.route(profile)

    if not decision.candidates:
        raise ValueError(f"No models match constraints for prompt {prompt_id}: {decision.reason}")

    # 3) Execute with fallback — selected first, then remaining candidates
    selected = decision.selected
    fallbacks = [c for c in decision.candidates if c.key != selected.key]
    chain = [selected] + fallbacks[:MAX_FALLBACK_ATTEMPTS - 1]
    attempts = 0
    last_error: Exception | None = None

    for candidate in chain:
        attempts += 1
        try:
            result = client.generate(
                prompt=row.raw_prompt,
                provider=candidate.provider,
                model=candidate.model,
                needs_web=profile.needs_web,
            )
            sources = [WebSource(**s) for s in result.sources] if result.sources else None
            return CompletionResponse(
                prompt_id=prompt_id,
                text=result.text,
                provider=candidate.provider,
                model=candidate.model,
                attempts=attempts,
                route_decision=decision,
                sources=sources,
            )
        except Exception as e:
            last_error = e

    raise RuntimeError(f"All {attempts} attempts failed. Last error: {last_error}")