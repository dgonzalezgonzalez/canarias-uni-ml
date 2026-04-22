import json
from pathlib import Path

from src.canarias_uni_ml.config import Settings
from src.canarias_uni_ml.embeddings.pipeline import run_embedding_pipeline


def test_embedding_pipeline_dry_run(tmp_path):
    input_path = Path("tests/fixtures/semantic_corpus.jsonl")
    output_path = tmp_path / "manifest.json"
    result = run_embedding_pipeline(
        input_path=str(input_path),
        output_path=str(output_path),
        provider_name="openai",
        model=None,
        dry_run=True,
        settings=Settings.from_env(),
    )
    assert result == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["provider"] == "openai"
    assert payload["dry_run"] is True
    assert payload["items"] == 2
