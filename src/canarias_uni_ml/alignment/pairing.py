from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(slots=True)
class CandidatePair:
    job_key: str
    degree_key: str
    job_title: str
    degree_title: str
    job_text: str
    degree_text: str
    job_text_hash: str
    degree_text_hash: str


def parse_pipe_values(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part.strip() for part in value.split("|") if part.strip()}


def build_candidate_pairs(jobs: list[dict], degrees: list[dict], *, min_text_len: int = 40) -> list[CandidatePair]:
    by_title: dict[str, list[dict]] = {}
    by_branch: dict[str, list[dict]] = {}
    titles_by_family: dict[str, set[str]] = {}
    for degree in degrees:
        title = (degree.get("title") or "").strip()
        branch = (degree.get("branch") or "").strip()
        if title:
            by_title.setdefault(title, []).append(degree)
            for family in _family_keys(title):
                titles_by_family.setdefault(family, set()).add(title)
        if branch:
            by_branch.setdefault(branch, []).append(degree)

    pairs: list[CandidatePair] = []
    seen: set[tuple[str, str]] = set()
    for idx, job in enumerate(jobs):
        if (job.get("degree_match_status") or "") != "matched":
            continue

        target_titles = parse_pipe_values(job.get("target_degree_titles"))
        target_branches = parse_pipe_values(job.get("target_degree_branches"))
        target_families = {
            family
            for title in target_titles
            for family in _family_keys(title)
        }

        matched_degrees: list[dict] = []
        for title in target_titles:
            for expanded_title in _expand_target_title(title, titles_by_family):
                matched_degrees.extend(by_title.get(expanded_title, []))
        for branch in target_branches:
            branch_rows = by_branch.get(branch, [])
            if not target_families:
                matched_degrees.extend(branch_rows)
                continue
            for degree in branch_rows:
                degree_title = (degree.get("title") or "").strip()
                degree_families = _family_keys(degree_title)
                if degree_families and degree_families.intersection(target_families):
                    matched_degrees.append(degree)

        job_text = (job.get("description") or job.get("title") or "").strip()
        if len(job_text) < min_text_len:
            continue

        job_key = _job_key(job, idx)
        for degree_idx, degree in enumerate(matched_degrees):
            degree_text = (degree.get("description") or degree.get("title") or "").strip()
            if len(degree_text) < min_text_len:
                continue
            degree_key = _degree_key(degree, degree_idx)
            dedup_key = (job_key, degree_key)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            pairs.append(
                CandidatePair(
                    job_key=job_key,
                    degree_key=degree_key,
                    job_title=(job.get("title") or "").strip(),
                    degree_title=(degree.get("title") or "").strip(),
                    job_text=job_text,
                    degree_text=degree_text,
                    job_text_hash="",
                    degree_text_hash="",
                )
            )

    return pairs


def _expand_target_title(title: str, titles_by_family: dict[str, set[str]]) -> set[str]:
    expanded = {title}
    for family in _family_keys(title):
        expanded.update(titles_by_family.get(family, set()))
    return expanded


def _family_keys(title: str) -> set[str]:
    """
    Conservative family normalization:
    - keeps only strongly related degree variants (same core program wording),
    - avoids broad fuzzy expansion that could pull unrelated programs.
    """
    norm = _norm(title)
    keys: set[str] = set()

    # "grado en psicologia - presencial ..." -> "psicologia"
    m = re.search(r"\bgrado en ([a-z0-9 ]+)", norm)
    if m:
        program = _clean_program_tail(m.group(1))
        if program:
            keys.add(program)

    # "doble grado en psicologia y criminologia" -> {"psicologia","criminologia"}
    d = re.search(r"\bdoble grado en ([a-z0-9 ]+)", norm)
    if d:
        chunk = _clean_program_tail(d.group(1))
        for part in [p.strip() for p in re.split(r"\by\b", chunk) if p.strip()]:
            keys.add(part)

    return keys


def _clean_program_tail(text: str) -> str:
    text = re.split(r"\bonline\b|\bpresencial\b|\bsemipresencial\b|\bmodalidad\b|\bduracion\b", text)[0]
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _job_key(job: dict, idx: int) -> str:
    source = (job.get("source") or "unknown").strip().lower()
    external_id = (job.get("external_id") or "").strip()
    if external_id:
        return f"job::{source}::{external_id}"
    source_url = (job.get("source_url") or "").strip()
    if source_url:
        return f"job_url::{source_url}"
    return f"job_row::{source}::{idx}"


def _degree_key(degree: dict, idx: int) -> str:
    source = (degree.get("source") or "unknown").strip().lower()
    source_id = (degree.get("source_id") or "").strip()
    if source_id:
        return f"degree::{source}::{source_id}"
    title = (degree.get("title") or "").strip().lower()
    return f"degree_row::{source}::{title}::{idx}"
