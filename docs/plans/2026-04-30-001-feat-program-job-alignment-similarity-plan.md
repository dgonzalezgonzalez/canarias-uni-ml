---
title: feat: Program-Job Alignment Similarity Pipeline
type: feat
status: completed
date: 2026-04-30
origin: docs/brainstorms/2026-04-22-job-degree-rule-mapping-requirements.md
---

# feat: Program-Job Alignment Similarity Pipeline

## Overview
Add an end-to-end alignment stage that embeds degree-program and job descriptions, computes cosine similarity only across sensible candidate pairs, and stores results in SQLite for analysis. The pipeline must support local Ollama for testing and OpenAI API for scale, with deterministic caching to skip already-embedded text.

## Problem Frame
The repository already produces job records and degree catalog records, and already annotates jobs with degree-target hints (`target_degree_branches`, `target_degree_titles`, `degree_match_status`). What is missing is the semantic scoring layer that quantifies alignment between each program and relevant jobs. This plan adds that layer and wires it into one master command.

## Requirements Trace
- R1. Compute embeddings for degree and job text and cosine similarity for relevant job-program pairs.
- R2. Restrict comparisons to sensible candidates using existing job-degree mapping fields to prevent incoherent matches.
- R3. Support provider abstraction for both OpenAI (`text-embedding-3-small` default) and local Ollama models.
- R4. Add embedding cache so unchanged text is not re-embedded on reruns.
- R5. Persist similarity outputs in SQLite with provenance (provider, model, timestamps, hashes).
- R6. Enable one master pipeline entrypoint to run scrape/catalog/embed/similarity sequence.
- R7. Update docs for usage, env vars, data contracts, and local-vs-cloud execution.
- R8. Prepare commit/PR-ready workflow for integration to GitHub.

## Scope Boundaries
- No ranking UI or dashboards in this phase.
- No fully-open all-vs-all similarity; candidate filtering remains mandatory.
- No irreversible migration away from current CSV artifacts; new DB tables are additive.

## Context & Research

### Relevant Code and Patterns
- Existing CLI domain routing in `src/canarias_uni_ml/cli.py`.
- Existing job scraping + upsert path in `src/canarias_uni_ml/jobs/pipeline.py` and `src/canarias_uni_ml/jobs/storage.py`.
- Existing deterministic candidate hints in `src/canarias_uni_ml/jobs/degree_mapping.py`.
- Existing embedding provider contract in `src/canarias_uni_ml/embeddings/providers/base.py` and OpenAI provider in `src/canarias_uni_ml/embeddings/providers/openai_provider.py`.
- Existing settings surface in `src/canarias_uni_ml/config.py`.

### Institutional Learnings
- `docs/brainstorms/2026-04-22-job-degree-rule-mapping-requirements.md` already established deterministic mapping and anti-absurd-match guardrails.
- Existing pipeline conventions prefer auditable status fields and rerunnable outputs.

### External References
- None required for plan viability; architecture can follow current repository patterns.

## Key Technical Decisions
- Candidate gate: use current `target_degree_titles` and `target_degree_branches` fields as first-pass pair filter.
Reason: reuses existing deterministic logic and enforces semantic scope.
- Cache key: hash normalized text + provider + model.
Reason: prevents stale cross-model reuse and enables exact rerun skipping.
- Similarity storage: SQLite table for embeddings metadata + pairwise scores.
Reason: scalable querying, joins, and reproducibility versus CSV-only storage.
- Provider strategy: keep provider interface and add Ollama provider alongside OpenAI.
Reason: local testing now, API scale later, no pipeline rewrite.
- Pipeline orchestration: add explicit master command, not hidden side effects in individual commands.
Reason: clearer operator control and easier CI/nightly adoption.

## Open Questions

### Resolved During Planning
- Input path ambiguity in user note (same CSV path repeated): plan assumes jobs come from `data/processed/canarias_jobs.csv` and degree text from degree outputs (`data/processed/degrees_catalog.csv` and/or `data/processed/degrees_descriptions.csv`) with fallback rules defined in implementation.
- Similarity scope: compute only for mapped candidate pairs, not all combinations.

### Deferred to Implementation
- Final minimum-text quality thresholds before embedding (exact character/token cutoffs).
- Final schema names for analytics-friendly materialized views.

## Implementation Units

- [x] **Unit 1: Define alignment data contracts and storage schema**

**Goal:** Establish stable artifacts/tables for cached embeddings and program-job similarity outputs.

**Requirements:** R1, R5

**Dependencies:** None

**Files:**
- Modify: `src/canarias_uni_ml/config.py`
- Create: `src/canarias_uni_ml/alignment/models.py`
- Create: `src/canarias_uni_ml/alignment/storage.py`
- Test: `tests/test_alignment_storage.py`

**Approach:**
- Add settings for alignment DB path and cache controls.
- Define tables for `embedding_cache` and `program_job_similarity` with unique keys and provenance fields.
- Add idempotent table creation and upsert behavior.

**Patterns to follow:**
- `src/canarias_uni_ml/jobs/storage.py` repository/upsert style.

**Test scenarios:**
- Happy path: schema initialization creates required tables and indexes.
- Happy path: upsert of same pair overwrites score/provenance deterministically.
- Edge case: duplicate cache key insertion remains single record.
- Error path: invalid DB path returns explicit storage error.

**Verification:**
- Fresh DB can be initialized and reused across reruns without duplicate explosion.

- [x] **Unit 2: Implement provider-flexible embedding service with cache-aware flow**

**Goal:** Produce embeddings through OpenAI or Ollama while skipping already-cached texts.

**Requirements:** R3, R4

**Dependencies:** Unit 1

**Files:**
- Modify: `src/canarias_uni_ml/embeddings/providers/base.py`
- Modify: `src/canarias_uni_ml/embeddings/pipeline.py`
- Create: `src/canarias_uni_ml/embeddings/providers/ollama_provider.py`
- Modify: `src/canarias_uni_ml/config.py`
- Test: `tests/test_embeddings_cache.py`
- Test: `tests/test_ollama_provider.py`

**Approach:**
- Extend provider registry to include `ollama` with configurable local endpoint/model.
- Split embedding pipeline into reusable service methods that return vectors plus cache metadata.
- Compute cache key from normalized text + provider + model; only call provider for misses.

**Execution note:** Start with failing cache behavior tests before provider refactor.

**Patterns to follow:**
- Existing provider abstraction in `src/canarias_uni_ml/embeddings/providers/`.

**Test scenarios:**
- Happy path: Ollama provider embeds sample batch and returns vectors.
- Happy path: OpenAI provider path remains backward compatible.
- Edge case: same text with different model creates separate cache entries.
- Error path: provider timeout/network error marks only affected batch, pipeline continues where possible.
- Integration: rerun with unchanged corpus yields zero provider calls for cached rows.

**Verification:**
- Second run over same inputs performs cache hits and materially fewer external/local embedding calls.

- [x] **Unit 3: Build candidate-pair generator and cosine similarity computation**

**Goal:** Generate valid job-program pairs and compute cosine similarity scores.

**Requirements:** R1, R2

**Dependencies:** Units 1-2

**Files:**
- Create: `src/canarias_uni_ml/alignment/pairing.py`
- Create: `src/canarias_uni_ml/alignment/similarity.py`
- Create: `src/canarias_uni_ml/alignment/pipeline.py`
- Test: `tests/test_alignment_pairing.py`
- Test: `tests/test_alignment_similarity.py`

**Approach:**
- Build pairing logic from job-side `target_degree_titles/branches` against degree catalog fields.
- Create normalized text selection rules (job description/title fallback; degree description/title fallback).
- Compute cosine similarity for each candidate pair and persist to alignment storage.

**Patterns to follow:**
- Mapping field semantics from `src/canarias_uni_ml/jobs/degree_mapping.py`.

**Test scenarios:**
- Happy path: mapped software job pairs only with informática-related degree rows.
- Edge case: job with empty mapping fields yields zero pairs and explicit status.
- Edge case: degree missing description falls back to eligible alternate text field.
- Error path: zero-vector or malformed embedding row is skipped with traceable status.
- Integration: pair generation + embedding retrieval + similarity write produces deterministic count and keys.

**Verification:**
- Stored similarity table contains only valid candidate pairs and score range is bounded [-1, 1].

- [x] **Unit 4: Integrate master orchestration command in CLI**

**Goal:** Run scraping/catalog/alignment in one command with configurable switches.

**Requirements:** R6

**Dependencies:** Units 1-3

**Files:**
- Modify: `src/canarias_uni_ml/cli.py`
- Create: `src/canarias_uni_ml/pipeline/master.py`
- Modify: `src/canarias_jobs/cli.py`
- Test: `tests/test_cli_master_pipeline.py`

**Approach:**
- Add a top-level command (for example `pipeline run`) that orchestrates jobs scrape, degree catalog refresh (optional), embedding stage, and similarity stage.
- Keep existing subcommands intact; master command composes them.
- Add flags for provider/model, cache reset policy, and dry-run.

**Patterns to follow:**
- Current CLI subparser pattern in `src/canarias_uni_ml/cli.py`.

**Test scenarios:**
- Happy path: master command executes stages in dependency order.
- Edge case: skip flags bypass selected stages but still execute downstream valid stages.
- Error path: upstream scrape failure aborts or degrades according to configured fail policy.
- Integration: master command writes both legacy artifacts and new alignment DB outputs.

**Verification:**
- Operator can run one command and obtain refreshed jobs plus similarity DB outputs.

- [x] **Unit 5: Documentation and delivery workflow updates**

**Goal:** Document new alignment pipeline, provider setup, and operational usage.

**Requirements:** R7, R8

**Dependencies:** Units 1-4

**Files:**
- Modify: `README.md`
- Create: `docs/alignment-pipeline.md`
- Modify: `docs/source-normalization.md`
- Modify: `requirements.txt`
- Test: `tests/test_readme_commands_smoke.py`

**Approach:**
- Add command examples for local Ollama testing and OpenAI production mode.
- Document env vars (`OPENAI_API_KEY`, Ollama host/model settings), cache behavior, and DB schema.
- Include commit/PR checklist section aligned with repository contribution norms.

**Patterns to follow:**
- Existing operational docs style in `docs/operations/*.md`.

**Test scenarios:**
- Integration: documented commands match real CLI arguments and expected outputs.

**Verification:**
- A new contributor can execute end-to-end pipeline from docs without reverse-engineering code.

## System-Wide Impact
- **Interaction graph:** Job scraping -> degree mapping hints -> embedding provider/cache -> cosine computation -> alignment DB.
- **Error propagation:** Provider/network errors should not corrupt cache; failed batch rows must be traceable.
- **State lifecycle risks:** Cache invalidation across model switches is critical; cache key design must encode provider/model.
- **API surface parity:** Existing `jobs`, `degrees`, `embed` commands remain supported while adding master orchestration.
- **Integration coverage:** Need cross-layer tests proving mapping-gated pairing plus persisted similarity outputs.
- **Unchanged invariants:** Existing CSV outputs remain canonical raw exports; alignment DB is additive.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Overly broad candidate pairing inflates compute and noise | Strict pairing gate from existing mapping fields and deterministic filters |
| Cache contamination across models/providers | Include provider+model in cache key and provenance columns |
| Ollama model variability across machines | Make model name and endpoint explicit config with startup validation |
| Upstream missing descriptions reduce coverage | Fallback text policy + explicit missing-text statuses in DB |

## Documentation / Operational Notes
- Keep a small local run profile (limited rows) for development validation.
- Reserve OpenAI usage for scale runs; local Ollama path should be default in examples for test mode.
- Add operational note for periodic cache compaction/pruning if DB grows.

## Sources & References
- **Origin document:** [docs/brainstorms/2026-04-22-job-degree-rule-mapping-requirements.md](docs/brainstorms/2026-04-22-job-degree-rule-mapping-requirements.md)
- Related code: `src/canarias_uni_ml/jobs/degree_mapping.py`, `src/canarias_uni_ml/embeddings/pipeline.py`, `src/canarias_uni_ml/cli.py`
