from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class EmbeddingResult:
    vectors: list[list[float]]
    usage: dict[str, int | str]


class EmbeddingProvider(Protocol):
    model: str

    def embed(self, texts: list[str]) -> EmbeddingResult:
        ...
