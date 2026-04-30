# Alignment Pipeline

This repository supports a program-job alignment stage based on text embeddings and cosine similarity.

## Goal

Measure how aligned each university program description is with labor-market demand from scraped job postings.

## Candidate Pairing Gate

Similarity is only computed for sensible pairs.

Job rows already include deterministic mapping fields:
- `target_degree_titles`
- `target_degree_branches`
- `degree_match_status`

The alignment stage only compares jobs with `degree_match_status=matched` and links them to degree rows by title/branch overlap.

## Embedding Providers

Supported providers:
- `openai` (production scale): default model `text-embedding-3-small`
- `ollama` (local testing): default model from `OLLAMA_EMBEDDING_MODEL`
- `groq` (kept for compatibility, embedding support depends on model availability)

Environment variables:

```bash
export OPENAI_API_KEY='sk-...'
export OLLAMA_BASE_URL='http://127.0.0.1:11434'
export OLLAMA_EMBEDDING_MODEL='nomic-embed-text'
```

## Caching

Embeddings are cached in SQLite (`embedding_cache` table) using a key derived from:
- normalized text hash
- provider name
- model name

This allows reruns to skip already embedded text while keeping model/provider separation.

## Output Database

Default database path:
- `data/processed/program_job_alignment.db`

Main tables:
- `embedding_cache`
- `program_job_similarity`

Each similarity row stores:
- job key
- degree key
- cosine score
- provider/model provenance
- text hashes
- timestamps

## Commands

Run alignment only:

```bash
python -m src.canarias_uni_ml.cli align run \
  --jobs-csv data/processed/canarias_jobs.csv \
  --degrees-csv data/processed/degrees_catalog.csv \
  --provider ollama
```

Run full pipeline from one command:

```bash
python -m src.canarias_uni_ml.cli pipeline run \
  --provider ollama
```

Scale-oriented run using OpenAI:

```bash
python -m src.canarias_uni_ml.cli pipeline run \
  --provider openai \
  --model text-embedding-3-small
```
