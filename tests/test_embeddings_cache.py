from src.canarias_uni_ml.alignment.storage import AlignmentRepository
from src.canarias_uni_ml.config import Settings
from src.canarias_uni_ml.embeddings.pipeline import embed_with_cache
from src.canarias_uni_ml.embeddings.providers.base import EmbeddingResult


class _FakeProvider:
    model = "fake"

    def __init__(self):
        self.calls = 0

    def embed(self, texts):
        self.calls += 1
        return EmbeddingResult(vectors=[[float(len(t))] for t in texts], usage={})


def test_embed_with_cache_reuses_vectors(monkeypatch, tmp_path):
    fake = _FakeProvider()

    def _fake_provider(name, model, settings):
        return fake

    monkeypatch.setattr("src.canarias_uni_ml.embeddings.pipeline._provider", _fake_provider)
    repo = AlignmentRepository(tmp_path / "alignment.db")
    settings = Settings.from_env()

    texts = ["hola mundo", "otro texto"]
    vectors1, hits1 = embed_with_cache(
        texts,
        provider_name="ollama",
        model="nomic-embed-text",
        settings=settings,
        repo=repo,
    )
    vectors2, hits2 = embed_with_cache(
        texts,
        provider_name="ollama",
        model="nomic-embed-text",
        settings=settings,
        repo=repo,
    )

    assert fake.calls == 1
    assert hits1 == 0
    assert hits2 == 2
    assert vectors1 == vectors2
