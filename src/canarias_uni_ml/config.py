from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    data_dir: Path = Path("data")
    processed_dir: Path = Path("data/processed")
    raw_dir: Path = Path("data/raw")
    jobs_output: Path = Path("data/processed/canarias_jobs.csv")
    jobs_db_output: Path = Path("data/processed/canarias_jobs.db")
    jobs_daemon_lock: Path = Path("data/processed/canarias_jobs.lock")
    degrees_catalog_output: Path = Path("data/processed/degrees_catalog.csv")
    degrees_db_output: Path = Path("data/processed/degrees_catalog.db")
    degrees_descriptions_output: Path = Path("data/processed/degrees_descriptions.csv")
    corpus_output: Path = Path("data/processed/semantic_corpus.jsonl")
    embeddings_manifest_output: Path = Path("data/processed/embeddings_manifest.json")
    alignment_db_output: Path = Path("data/processed/program_job_alignment.db")
    openai_api_key: str | None = None
    groq_api_key: str | None = None
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_embedding_model: str = "nomic-embed-text"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            groq_api_key=os.getenv("GROQ_API_KEY"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            ollama_embedding_model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        )
