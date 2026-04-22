from __future__ import annotations

from .base import EmbeddingProvider, EmbeddingResult


class GroqEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str = "unknown-groq-embedding-model") -> None:
        self.api_key = api_key
        self.model = model

    def embed(self, texts: list[str]) -> EmbeddingResult:
        raise RuntimeError(
            "Groq embedding support not verified in this repository yet. "
            "Use dry-run or OpenAI provider until a compatible embedding model is confirmed."
        )
