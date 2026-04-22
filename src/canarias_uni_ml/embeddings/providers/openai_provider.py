from __future__ import annotations

import httpx

from .base import EmbeddingProvider, EmbeddingResult


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        self.api_key = api_key
        self.model = model
        self.client = httpx.Client(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0,
        )

    def embed(self, texts: list[str]) -> EmbeddingResult:
        response = self.client.post("/embeddings", json={"model": self.model, "input": texts})
        response.raise_for_status()
        payload = response.json()
        vectors = [item["embedding"] for item in payload.get("data", [])]
        usage = payload.get("usage", {})
        usage["model"] = self.model
        return EmbeddingResult(vectors=vectors, usage=usage)
