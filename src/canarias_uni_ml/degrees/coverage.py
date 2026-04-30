from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass(slots=True)
class DescriptionCoverage:
    total: int
    described: int
    ratio: float
    by_source: dict[str, int]


def compute_description_coverage(rows: list[dict]) -> DescriptionCoverage:
    total = len(rows)
    described_rows = [row for row in rows if (row.get("description") or "").strip() and row.get("description_status") == "ok"]
    described = len(described_rows)
    ratio = described / total if total else 0.0
    source_counter = Counter((row.get("description_source_type") or "") for row in described_rows)
    return DescriptionCoverage(total=total, described=described, ratio=ratio, by_source=dict(source_counter))


def ensure_min_description_coverage(rows: list[dict], minimum: float | None) -> tuple[bool, str]:
    coverage = compute_description_coverage(rows)
    message = (
        f"description coverage: {coverage.described}/{coverage.total} "
        f"({coverage.ratio:.2%}) by source={coverage.by_source}"
    )
    if minimum is None:
        return True, message
    return coverage.ratio >= minimum, message
