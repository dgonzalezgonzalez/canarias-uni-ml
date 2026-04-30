from __future__ import annotations

from dataclasses import dataclass

from .program_validation import is_allowed_program_url, is_program_title, normalize_for_match
from .university_registry import load_canary_university_registry

REQUIRED_TITLE_TYPES = ("grado", "master", "doctorado")


@dataclass(slots=True)
class InventoryCompleteness:
    expected_universities: int
    observed_universities: int
    university_ratio: float
    missing_university_ids: tuple[str, ...]
    expected_title_types: int
    observed_title_types: int
    title_type_ratio: float
    missing_title_types: tuple[str, ...]
    missing_university_title_type_pairs: tuple[tuple[str, str], ...]


@dataclass(slots=True)
class CatalogQuality:
    ok: bool
    blocked_rows: tuple[str, ...]


def compute_inventory_completeness(
    rows: list[dict],
    *,
    required_university_ids: tuple[str, ...] | None = None,
    required_title_types: tuple[str, ...] = REQUIRED_TITLE_TYPES,
) -> InventoryCompleteness:
    if required_university_ids is None:
        required_university_ids = tuple(entry.university_id for entry in load_canary_university_registry())

    expected_university_set = set(required_university_ids)
    observed_university_set = {
        (row.get("university_id") or "").strip().lower()
        for row in rows
        if (row.get("university_id") or "").strip().lower() in expected_university_set
    }
    missing_university_ids = tuple(sorted(expected_university_set - observed_university_set))

    required_types_set = {item.strip().lower() for item in required_title_types if item.strip()}
    observed_types_set = {
        (row.get("title_type") or "").strip().lower()
        for row in rows
        if (row.get("title_type") or "").strip().lower() in required_types_set
    }
    missing_title_types = tuple(sorted(required_types_set - observed_types_set))
    expected_pairs = {(university_id, title_type) for university_id in expected_university_set for title_type in required_types_set}
    observed_pairs = {
        ((row.get("university_id") or "").strip().lower(), (row.get("title_type") or "").strip().lower())
        for row in rows
        if (row.get("university_id") or "").strip().lower() in expected_university_set
        and (row.get("title_type") or "").strip().lower() in required_types_set
    }
    missing_pairs = tuple(sorted(expected_pairs - observed_pairs))

    expected_universities = len(expected_university_set)
    expected_title_types = len(required_types_set)
    observed_universities = len(observed_university_set)
    observed_title_types = len(observed_types_set)

    university_ratio = (observed_universities / expected_universities) if expected_universities else 0.0
    title_type_ratio = (observed_title_types / expected_title_types) if expected_title_types else 0.0

    return InventoryCompleteness(
        expected_universities=expected_universities,
        observed_universities=observed_universities,
        university_ratio=university_ratio,
        missing_university_ids=missing_university_ids,
        expected_title_types=expected_title_types,
        observed_title_types=observed_title_types,
        title_type_ratio=title_type_ratio,
        missing_title_types=missing_title_types,
        missing_university_title_type_pairs=missing_pairs,
    )


def ensure_min_inventory_completeness(
    rows: list[dict],
    minimum: float | None,
    *,
    require_all_scoped_universities: bool = False,
    required_title_types: tuple[str, ...] = REQUIRED_TITLE_TYPES,
) -> tuple[bool, str]:
    completeness = compute_inventory_completeness(rows, required_title_types=required_title_types)
    message = (
        f"inventory completeness (universities): {completeness.observed_universities}/{completeness.expected_universities} "
        f"({completeness.university_ratio:.2%}), missing_university_ids={list(completeness.missing_university_ids)}; "
        f"title_types: {completeness.observed_title_types}/{completeness.expected_title_types} "
        f"({completeness.title_type_ratio:.2%}), missing_title_types={list(completeness.missing_title_types)}; "
        f"missing_university_title_type_pairs={list(completeness.missing_university_title_type_pairs)}"
    )
    ok_ratio = True if minimum is None else completeness.university_ratio >= minimum
    ok_universities = (not require_all_scoped_universities) or not completeness.missing_university_ids
    return ok_ratio and ok_universities, message


def validate_degree_catalog_quality(rows: list[dict]) -> CatalogQuality:
    blocked: list[str] = []
    for index, row in enumerate(rows, start=1):
        title = row.get("title") or ""
        title_type = row.get("title_type") or ""
        source_url = row.get("source_url") or ""
        normalized_title = normalize_for_match(title)
        if not title_type.strip():
            blocked.append(f"row {index}: blank title_type title={title!r}")
            continue
        if "@" in normalized_title or not is_program_title(title, title_type):
            blocked.append(f"row {index}: non-program title={title!r}")
            continue
        if not is_allowed_program_url(source_url):
            blocked.append(f"row {index}: non-program source_url={source_url!r} title={title!r}")
    return CatalogQuality(ok=not blocked, blocked_rows=tuple(blocked))
