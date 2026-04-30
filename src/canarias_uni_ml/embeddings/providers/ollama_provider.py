from __future__ import annotations

import httpx

from .base import EmbeddingProvider, EmbeddingResult


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: str, base_url: str = "http://127.0.0.1:11434") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=60.0)

    def embed(self, texts: list[str]) -> EmbeddingResult:
        vectors: list[list[float]] = []
        for text in texts:
            response = self.client.post("/api/embeddings", json={"model": self.model, "prompt": text})
            response.raise_for_status()
            payload = response.json()
            vectors.append(payload.get("embedding", []))
        return EmbeddingResult(vectors=vectors, usage={"model": self.model, "provider": "ollama"})
