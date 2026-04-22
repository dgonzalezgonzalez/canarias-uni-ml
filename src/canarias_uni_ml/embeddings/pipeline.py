from __future__ import annotations

import json
from pathlib import Path

from ..config import Settings
from ..io import ensure_parent
from .chunking import chunk_text
from .providers.groq_provider import GroqEmbeddingProvider
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


def _provider(name: str, model: str | None, settings: Settings):
    if name == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY missing")
        return OpenAIEmbeddingProvider(settings.openai_api_key, model or "text-embedding-3-small")
    if name == "groq":
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY missing")
        return GroqEmbeddingProvider(settings.groq_api_key, model or "unknown-groq-embedding-model")
    raise RuntimeError(f"Unsupported provider: {name}")


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

    manifest = {
        "provider": provider_name,
        "model": model or ("text-embedding-3-small" if provider_name == "openai" else "unknown-groq-embedding-model"),
        "items": len(corpus),
        "chunks": len(texts),
        "estimated_tokens": _estimate_tokens(texts),
        "dry_run": dry_run,
    }

    if not dry_run and texts:
        provider = _provider(provider_name, model, settings)
        result = provider.embed(texts)
        manifest["usage"] = result.usage
        manifest["vector_count"] = len(result.vectors)

    ensure_parent(output_path)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    print(f"[done] wrote embedding manifest to {output_path}")
    return 0
