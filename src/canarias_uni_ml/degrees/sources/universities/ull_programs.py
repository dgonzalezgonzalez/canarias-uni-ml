from __future__ import annotations

from .programs import ProgramCandidate, parse_anchor_programs


def parse_ull_programs(html: str, *, page_url: str, title_type: str | None = None) -> list[ProgramCandidate]:
    return parse_anchor_programs(html, page_url=page_url, default_title_type=title_type)
