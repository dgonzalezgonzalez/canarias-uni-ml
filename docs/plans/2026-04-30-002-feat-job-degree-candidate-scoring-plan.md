---
title: feat: Improve Job-Degree Matching with Relative Score Selection
type: feat
status: completed
date: 2026-04-30
origin: docs/brainstorms/2026-04-30-job-degree-candidate-scoring-requirements.md
---

# feat: Improve Job-Degree Matching with Relative Score Selection

## Overview
Replace noisy branch-based title expansion in job-degree mapping with a scored candidate selector that uses title-only relevance, per-job relative thresholding, and explicit no-match behavior for weak evidence.

## Problem Frame
Current mapping in `src/canarias_uni_ml/jobs/degree_mapping.py` expands all degree titles from matched branches. This causes incoherent matches (for example, science teacher postings paired with unrelated humanities/arts titles), which pollutes downstream cosine-similarity outputs.

## Requirements Trace
- R1. Build candidate title list from degree catalog titles.
- R2. Score each `(job, degree_title)` using title-only relevance.
- R3. Keep titles where `score >= best_score - 0.15`.
- R4. Cap kept titles at `max_keep = 8`.
- R5. Permit `no_match` when confidence is weak.
- R6. Write selected titles to `target_degree_titles`.
- R7. Support explicit unmatched status.
- R8. Preserve compatibility with downstream alignment consuming `target_degree_titles`.
- R9. Remove broad branch-to-all-titles expansion behavior.
- R10. Keep deterministic output ordering.
- R11. Add scoring diagnostics for auditability.

## Scope Boundaries
- In scope: mapping logic, status semantics, diagnostics, tests.
- Out of scope: embedding model changes, cosine computation changes, UI/reporting.

## Context & Research

### Relevant Code and Patterns
- `src/canarias_uni_ml/jobs/degree_mapping.py` currently performs rule matching and branch expansion.
- `tests/test_degree_mapping.py` currently validates guaranteed-title and branch-expansion behavior.
- `src/canarias_uni_ml/jobs/pipeline.py` consumes mapper output and persists fields for downstream alignment.

### Institutional Learnings
- Existing deterministic mapping is required for auditability.
- Quality issue now is precision, not missing broad-coverage fallback.

### External References
- None required; this is internal matching policy refinement.

## Key Technical Decisions
- Use title-only lexical scoring (no embedding call in mapper).
Reason: fast, deterministic, and aligned with chosen brainstorm direction.
- Use relative threshold with `delta=0.15`.
Reason: flexible candidate count per job without hard fixed-K behavior.
- Enforce `max_keep=8`.
Reason: prevent candidate explosion while preserving multiple plausible degrees.
- Allow explicit `no_match` when low confidence.
Reason: avoid arbitrary noisy fallback titles.

## Open Questions

### Resolved During Planning
- Keep compatibility with existing output fields (`target_degree_titles`, `target_degree_branches`, `degree_match_status`) rather than introducing a new schema.

### Deferred to Implementation
- Exact weak-confidence floor value (global minimum score) that triggers `no_match`.
- Final diagnostic surface (CSV/debug fields vs optional sidecar logs).

## Implementation Units

- [x] **Unit 1: Introduce title scoring primitives and candidate builder**

**Goal:** Add deterministic title-only scoring and candidate generation utilities.

**Requirements:** R1, R2, R10

**Dependencies:** None

**Files:**
- Modify: `src/canarias_uni_ml/jobs/degree_mapping.py`
- Test: `tests/test_degree_mapping.py`

**Approach:**
- Add normalized token overlap / lexical scoring helper for job text vs degree title.
- Build candidate pool from catalog titles (optionally branch-prioritized, but not branch-expanded-all).
- Keep deterministic sorting on score desc, then title asc.

**Patterns to follow:**
- Existing normalization helpers `_norm`, `_rule_matches` in `degree_mapping.py`.

**Test scenarios:**
- Happy path: software job ranks informatics degree above unrelated titles.
- Edge case: accents/punctuation normalization still matches equivalent forms.
- Edge case: tie score ordering deterministic across reruns.

**Verification:**
- Same input rows produce identical scored ordering across repeated runs.

- [x] **Unit 2: Apply relative-threshold selector with no-match handling**

**Goal:** Replace branch-wide title expansion with threshold-based dynamic selection.

**Requirements:** R3, R4, R5, R6, R7, R9

**Dependencies:** Unit 1

**Files:**
- Modify: `src/canarias_uni_ml/jobs/degree_mapping.py`
- Test: `tests/test_degree_mapping.py`

**Approach:**
- Compute best score per job.
- Keep candidates where `score >= best_score - 0.15`.
- Limit kept titles to first 8 after deterministic ranking.
- If no candidate passes confidence policy, set titles empty and `degree_match_status=no_match`.
- Remove forced `fallback_title` behavior for weak-evidence cases.

**Execution note:** Start test-first for current bad regression (science teacher case).

**Patterns to follow:**
- Existing `degree_match_status` output conventions in mapper and job pipeline.

**Test scenarios:**
- Happy path: strong teaching science job keeps science-relevant degrees.
- Edge case: many close candidates gets capped at 8.
- Edge case: one clearly best candidate yields single kept title.
- Error path: empty/low-signal job text yields `no_match` without fallback title.

**Verification:**
- Known incoherent matches disappear from selected titles in regression fixtures.

- [x] **Unit 3: Add mapping diagnostics and preserve pipeline compatibility**

**Goal:** Make selection auditable without breaking downstream consumers.

**Requirements:** R8, R11

**Dependencies:** Unit 2

**Files:**
- Modify: `src/canarias_uni_ml/jobs/degree_mapping.py`
- Modify: `src/canarias_uni_ml/jobs/models.py` (if diagnostics fields are persisted)
- Modify: `src/canarias_uni_ml/jobs/pipeline.py` (only if needed for export)
- Test: `tests/test_jobs_pipeline.py`

**Approach:**
- Add per-job diagnostics (best score, kept count; optional top candidate snapshot).
- Keep `target_degree_titles` and `degree_match_status` contract unchanged for alignment stage.
- Ensure downstream alignment still uses selected titles directly.

**Patterns to follow:**
- Existing additive-field evolution style in `JobRecord` and CSV export.

**Test scenarios:**
- Integration: jobs pipeline outputs selected titles + statuses with no parser break.
- Integration: alignment stage can still form job-degree pairs from `target_degree_titles`.

**Verification:**
- Full jobs CSV remains parseable and alignment pairing logic consumes updated fields without schema errors.

- [x] **Unit 4: Refresh fixtures and regression tests for precision outcomes**

**Goal:** Lock in improved precision and prevent branch-expansion regression.

**Requirements:** R2, R3, R5, R9, R10

**Dependencies:** Units 1-3

**Files:**
- Modify: `tests/test_degree_mapping.py`
- Create: `tests/fixtures/degree_mapping_jobs_precision.csv` (or equivalent fixture file)

**Approach:**
- Add explicit regression sample for science-teacher posting.
- Remove outdated test that expects branch expansion to include unrelated titles.
- Add assertions for `no_match` behavior.

**Patterns to follow:**
- Current fixture-driven mapper tests.

**Test scenarios:**
- Happy path: science teacher includes physics/chemistry/biology-aligned degrees, excludes unrelated arts/humanities.
- Edge case: weak generic job title returns `no_match`.
- Integration: rerun stable ordering and stable kept count given fixed catalog.

**Verification:**
- Test suite fails on old branch-expansion behavior and passes with new scoring selector.

## System-Wide Impact
- **Interaction graph:** job scraper output -> degree mapper -> jobs CSV -> alignment pair builder.
- **Error propagation:** weak signal should propagate as explicit `no_match`, not hidden fallback title.
- **State lifecycle risks:** changing status semantics may affect downstream analytics filters.
- **API surface parity:** no breaking output column removal; field meanings become stricter.
- **Integration coverage:** need cross-test from mapping output into alignment pairing.
- **Unchanged invariants:** alignment stage still consumes `target_degree_titles` as authoritative candidate set.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Over-pruning valid degree options | Tune threshold floor and verify on manual sample |
| Under-pruning noisy titles | Add science-teacher regression plus cap=8 guardrail |
| Status semantic drift (`matched` vs `no_match`) | Document and test explicit status transitions |
| Hidden downstream dependency on guaranteed title | Add integration test and update docs if behavior changes |

## Documentation / Operational Notes
- Update README or source notes to describe new matching policy and `no_match` behavior.
- Record threshold and cap constants in one location for future retuning.

## Sources & References
- **Origin document:** [docs/brainstorms/2026-04-30-job-degree-candidate-scoring-requirements.md](docs/brainstorms/2026-04-30-job-degree-candidate-scoring-requirements.md)
- Related code: `src/canarias_uni_ml/jobs/degree_mapping.py`, `tests/test_degree_mapping.py`, `src/canarias_uni_ml/jobs/pipeline.py`
