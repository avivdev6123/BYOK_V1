#python - <<'EOF'
from pathlib import Path

paths = [
    "byok-router/app/api/v1",
    "byok-router/app/schemas",
    "byok-router/app/services",
    "byok-router/app/providers",
    "byok-router/app/utils",
    "byok-router/tests/unit",
]

files = [
    "byok-router/pyproject.toml",
    "byok-router/pytest.ini",
    "byok-router/Makefile",
    "byok-router/README.md",
    "byok-router/.env.example",
    "byok-router/app/main.py",
    "byok-router/app/api/v1/routes_generate.py",
    "byok-router/app/schemas/generate.py",
    "byok-router/app/services/router.py",
    "byok-router/app/services/cost.py",
    "byok-router/app/services/validator.py",
    "byok-router/app/utils/token_estimator.py",
    "byok-router/app/providers/base.py",
    "byok-router/app/providers/openai_adapter.py",
    "byok-router/app/providers/gemini_adapter.py",
    "byok-router/tests/unit/test_cost.py",
    "byok-router/tests/unit/test_validator.py",
    "byok-router/tests/unit/test_router.py",
]

for p in paths:
    Path(p).mkdir(parents=True, exist_ok=True)

for f in files:
    Path(f).touch()

print("BYOK project skeleton created.")
#EOF
