from __future__ import annotations


def chunk_text(text: str, max_chars: int = 3000) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if len(cleaned) <= max_chars:
        return [cleaned]
    return [cleaned[index:index + max_chars] for index in range(0, len(cleaned), max_chars)]
