from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CandidatePair:
    job_key: str
    degree_key: str
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
    for degree in degrees:
        title = (degree.get("title") or "").strip()
        branch = (degree.get("branch") or "").strip()
        if title:
            by_title.setdefault(title, []).append(degree)
        if branch:
            by_branch.setdefault(branch, []).append(degree)

    pairs: list[CandidatePair] = []
    seen: set[tuple[str, str]] = set()
    for idx, job in enumerate(jobs):
        if (job.get("degree_match_status") or "") != "matched":
            continue

        target_titles = parse_pipe_values(job.get("target_degree_titles"))
        target_branches = parse_pipe_values(job.get("target_degree_branches"))

        matched_degrees: list[dict] = []
        for title in target_titles:
            matched_degrees.extend(by_title.get(title, []))
        for branch in target_branches:
            matched_degrees.extend(by_branch.get(branch, []))

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
                    job_text=job_text,
                    degree_text=degree_text,
                    job_text_hash="",
                    degree_text_hash="",
                )
            )

    return pairs


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
