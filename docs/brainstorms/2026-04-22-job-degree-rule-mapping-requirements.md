---
date: 2026-04-22
topic: job-degree-rule-mapping
---

# Job to Degree Rule Mapping

## Problem Frame
Current jobs dataset (`data/processed/canarias_jobs.csv`) has no structured field linking each job to suitable university studies. Team needs deterministic, auditable mapping so future joins with `data/processed/degrees_catalog.csv` avoid nonsensical matches (example: gardening role mapped to engineering degree).

## Requirements

**Output Fields**
- R1. Each job row must include `target_degree_branches` as a pipe-separated list of branch labels aligned with `degrees_catalog.csv` values.
- R2. Each job row must include `target_degree_titles` as a pipe-separated list of degree title labels aligned with `degrees_catalog.csv` values.
- R3. Each job row must include `degree_match_status` to indicate mapping outcome.

**Matching Logic**
- R4. Mapping method must be rule-based dictionary only (no semantic similarity or ML in this phase).
- R5. Rules must use job-side signals (at least title, optionally description) and assign one or more branch/title targets when confidence is clear.
- R6. Mapping must prevent clearly incoherent pairings by design (for example manual/sector-specific roles mapped to unrelated academic families).

**Fallback Behavior**
- R7. If no rule applies, keep `target_degree_branches` and `target_degree_titles` empty.
- R8. If no rule applies, set `degree_match_status=no_rule`.

## Success Criteria
- At least one deterministic mapping status exists for every job row.
- Mapped branch/title values are directly joinable against values present in `degrees_catalog.csv`.
- Manual spot check on sampled roles confirms semantic coherence and no obvious absurd matches.
- Unmapped rows are explicit (`no_rule`) rather than silently dropped or weakly forced.

## Scope Boundaries
- No embedding/similarity model in this phase.
- No probabilistic confidence scoring in this phase.
- No automatic inference for unknown roles beyond explicit dictionary rules.

## Key Decisions
- Mapping strategy: Rule dictionary only.
Reason: Maximum control and auditability for first version.
- Stored outputs: Both branches and titles.
Reason: Branch gives robust coarse filtering; title enables finer future joins.
- Unknown-role fallback: Empty targets + `degree_match_status=no_rule`.
Reason: Avoid false precision and bad downstream joins.

## Dependencies / Assumptions
- `degrees_catalog.csv` remains current source of valid degree titles/branches.
- Rule authors can maintain a curated dictionary over time as new job patterns appear.

## Outstanding Questions

### Resolve Before Planning
- None.

### Deferred to Planning
- [R4][Technical] Where to persist and version rule dictionary (flat YAML/CSV/Python map) while preserving easy edits.
- [R5][Needs research] Which normalization layer should canonicalize job text before rule matching for stability.
- [R1][Needs research] Whether output order of multiple titles/branches should be deterministic by priority, alphabetic, or rule order.

## Next Steps
-> /ce:plan for structured implementation planning
