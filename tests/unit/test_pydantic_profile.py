from app.schemas.prompts import PromptProfile

valid_data = {
    "task_type": "coding",
    "needs_web": False,
    "needs_code": True,
    "output_format": "text",
    "urgency": "normal",
    "confidence": 0.82
}

profile = PromptProfile(**valid_data)
print(profile)