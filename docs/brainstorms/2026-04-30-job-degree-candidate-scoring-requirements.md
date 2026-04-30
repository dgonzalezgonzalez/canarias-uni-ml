---
date: 2026-04-30
topic: job-degree-candidate-scoring
---

# Job-Degree Candidate Scoring (Precision Upgrade)

## Problem Frame
Current job-to-degree mapping over-expands degree titles from broad branch mappings, producing clearly incoherent pairs (example: science-teacher jobs paired with unrelated humanities/art degrees). This reduces trust in downstream cosine-similarity outputs.

## Goal
Replace branch-expansion title assignment with flexible scored candidate selection that prioritizes precision while preserving coverage.

## Decisions Locked During Brainstorm
- Direction: scored candidates (not fixed rule-only list, not full branch expansion)
- Candidate count policy: flexible per job (not fixed K)
- Selection rule: per-job relative threshold
- Relative threshold: `delta = 0.15` (keep degree if `score >= best_score - 0.15`)
- Max candidates safety cap: `max_keep = 8`
- Base scoring signal: title-only
- Low-confidence behavior: allow `no_match` (do not force at least one degree)

## Requirements

### Core Behavior
- R1. For each job, generate degree candidates from existing degree catalog (titles available in `data/processed/degrees_catalog.csv`).
- R2. Compute a title-only relevance score per `(job, degree)` candidate.
- R3. Select candidates dynamically per job using relative threshold:
  - Let `best_score = max(candidate_scores)`
  - Keep candidate if `score >= best_score - 0.15`
- R4. Apply upper bound `max_keep = 8` per job after threshold filtering.
- R5. Do **not** force fallback degree when evidence is weak; permit `no_match` outcome.

### Output Contract
- R6. `target_degree_titles` must contain only selected high-relevance degrees (pipe-separated).
- R7. `degree_match_status` must support explicit low-confidence outcome (e.g., `no_match` / `no_rule`) when no candidate passes quality criteria.
- R8. Existing downstream alignment stage must continue consuming `target_degree_titles` without interface break.

### Quality Controls
- R9. Remove/disable broad branch-to-all-titles expansion behavior that currently inflates noise.
- R10. Preserve deterministic output ordering (stable reruns on same inputs).
- R11. Add traceable per-job scoring diagnostics sufficient for audit/debug (at least best score and kept count; full candidate logs optional but preferred).

## Success Criteria
- SC1. Known bad examples (science-teacher postings) no longer include clearly unrelated degrees.
- SC2. Precision improves on manual spot-check sample compared with current branch-expansion baseline.
- SC3. `target_degree_titles` average size per job decreases from noisy baseline while retaining meaningful coverage.
- SC4. Jobs with weak evidence are explicitly marked as unmatched instead of receiving arbitrary fallback titles.

## Scope Boundaries
- In scope:
  - Candidate scoring and selection for job-degree mapping
  - Output status behavior for low confidence
  - Test coverage for edge cases and regression examples
- Out of scope:
  - Embedding model changes
  - Cosine similarity formula changes
  - UI/reporting redesign

## Risks / Open Questions for Planning
- Need concrete title-only scoring function choice (token overlap, weighted n-gram, BM25-like, etc.).
- Need explicit low-confidence cutoff policy in addition to relative threshold (to avoid keeping weak but relatively best candidates).
- Need migration strategy for compatibility with prior `degree_match_status` semantics.

## Next Step
Proceed with `/ce:plan` to define implementation units, tests, and rollout details.
