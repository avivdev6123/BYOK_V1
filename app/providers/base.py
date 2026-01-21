from abc import ABC, abstractmethod

class ProviderAdapter(ABC):
    @abstractmethod
    async def generate(self, prompt: str, max_output_tokens: int, require_json: bool) -> str:
        ...
