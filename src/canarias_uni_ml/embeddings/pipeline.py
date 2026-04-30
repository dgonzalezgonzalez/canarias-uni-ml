from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..config import Settings
from ..io import ensure_parent
from ..alignment.storage import AlignmentRepository
from .chunking import chunk_text
from .providers.base import EmbeddingProvider
from .providers.groq_provider import GroqEmbeddingProvider
from .providers.ollama_provider import OllamaEmbeddingProvider
from .providers.openai_provider import OpenAIEmbeddingProvider


def _load_corpus(input_path: str) -> list[dict]:
    path = Path(input_path)
    if not path.exists():
        return []
    rows: list[dict] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _estimate_tokens(texts: list[str]) -> int:
    return sum(max(1, len(text) // 4) for text in texts)


def normalize_text(text: str) -> str:
    return " ".join(text.split()).strip()


def text_hash(text: str) -> str:
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def cache_key(*, provider_name: str, model: str, text: str) -> str:
    return hashlib.sha256(f"{provider_name}:{model}:{text_hash(text)}".encode("utf-8")).hexdigest()


def _provider(name: str, model: str | None, settings: Settings) -> EmbeddingProvider:
    if name == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY missing")
        return OpenAIEmbeddingProvider(settings.openai_api_key, model or "text-embedding-3-small")
    if name == "groq":
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY missing")
        return GroqEmbeddingProvider(settings.groq_api_key, model or "unknown-groq-embedding-model")
    if name == "ollama":
        return OllamaEmbeddingProvider(
            model=model or settings.ollama_embedding_model,
            base_url=settings.ollama_base_url,
        )
    raise RuntimeError(f"Unsupported provider: {name}")


def embed_with_cache(
    texts: list[str],
    *,
    provider_name: str,
    model: str,
    settings: Settings,
    repo: AlignmentRepository,
) -> tuple[list[list[float]], int]:
    vectors: list[list[float]] = []
    cache_hits = 0
    misses: list[tuple[int, str, str]] = []

    for idx, text in enumerate(texts):
        key = cache_key(provider_name=provider_name, model=model, text=text)
        cached = repo.get_cached_vector(key)
        if cached is not None:
            vectors.append(cached)
            cache_hits += 1
            continue
        vectors.append([])
        misses.append((idx, key, text))

    if misses:
        provider = _provider(provider_name, model, settings)
        miss_vectors = provider.embed([text for _, _, text in misses]).vectors
        for (idx, key, text), vector in zip(misses, miss_vectors):
            vectors[idx] = vector
            repo.upsert_cached_vector(
                cache_key=key,
                text_hash=text_hash(text),
                provider=provider_name,
                model=model,
                vector=vector,
            )

    return vectors, cache_hits


def run_embedding_pipeline(
    input_path: str,
    output_path: str,
    provider_name: str,
    model: str | None,
    dry_run: bool,
    settings: Settings,
) -> int:
    corpus = _load_corpus(input_path)
    texts = []
    for row in corpus:
        texts.extend(chunk_text(row.get("text", "")))

    active_model = model or (
        "text-embedding-3-small" if provider_name == "openai" else settings.ollama_embedding_model
        if provider_name == "ollama"
        else "unknown-groq-embedding-model"
    )

    manifest = {
        "provider": provider_name,
        "model": active_model,
        "items": len(corpus),
        "chunks": len(texts),
        "estimated_tokens": _estimate_tokens(texts),
        "dry_run": dry_run,
    }

    if not dry_run and texts:
        repo = AlignmentRepository(settings.alignment_db_output)
        vectors, cache_hits = embed_with_cache(
            texts,
            provider_name=provider_name,
            model=active_model,
            settings=settings,
            repo=repo,
        )
        manifest["vector_count"] = len(vectors)
        manifest["cache_hits"] = cache_hits
        manifest["cache_misses"] = len(vectors) - cache_hits

    ensure_parent(output_path)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    print(f"[done] wrote embedding manifest to {output_path}")
    return 0
