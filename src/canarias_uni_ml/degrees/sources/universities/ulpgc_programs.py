from __future__ import annotations

from .programs import ProgramCandidate, dedupe_candidates, parse_anchor_programs, parse_heading_programs


def parse_ulpgc_programs(html: str, *, page_url: str, title_type: str | None = None) -> list[ProgramCandidate]:
    candidates = parse_heading_programs(html, page_url=page_url, default_title_type=title_type)
    if title_type == "doctorado":
        candidates.extend(parse_anchor_programs(html, page_url=page_url, default_title_type=title_type))
    return dedupe_candidates(candidates)
