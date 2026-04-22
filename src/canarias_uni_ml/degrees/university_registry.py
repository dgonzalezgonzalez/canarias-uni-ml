from __future__ import annotations

import csv
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DEFAULT_REGISTRY_PATH = Path("data/reference/canary_universities.csv")


@dataclass(frozen=True, slots=True)
class UniversityRegistryEntry:
    university_id: str
    canonical_name: str
    university_type: str
    aliases: tuple[str, ...]


@lru_cache(maxsize=1)
def load_canary_university_registry(path: str | Path = DEFAULT_REGISTRY_PATH) -> tuple[UniversityRegistryEntry, ...]:
    rows: list[UniversityRegistryEntry] = []
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            aliases = tuple(_normalize_for_match(x) for x in (row.get("aliases") or "").split("|") if x.strip())
            canonical = row.get("canonical_name", "").strip()
            rows.append(
                UniversityRegistryEntry(
                    university_id=(row.get("university_id") or "").strip(),
                    canonical_name=canonical,
                    university_type=(row.get("university_type") or "").strip(),
                    aliases=tuple(dict.fromkeys((_normalize_for_match(canonical), *aliases))),
                )
            )
    return tuple(rows)


def match_canary_university(name: str | None, path: str | Path = DEFAULT_REGISTRY_PATH) -> UniversityRegistryEntry | None:
    normalized = _normalize_for_match(name)
    if not normalized:
        return None
    for entry in load_canary_university_registry(path):
        if normalized in entry.aliases:
            return entry
    return None


def _normalize_for_match(text: str | None) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", text)
    no_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return " ".join(no_accents.lower().split())
