from src.canarias_uni_ml.embeddings.providers.ollama_provider import OllamaEmbeddingProvider


class _Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {"embedding": [0.1, 0.2, 0.3]}


class _Client:
    def __init__(self):
        self.calls = 0

    def post(self, path, json):
        assert path == "/api/embeddings"
        assert "model" in json
        assert "prompt" in json
        self.calls += 1
        return _Response()


def test_ollama_provider_embed_batch():
    provider = OllamaEmbeddingProvider(model="nomic-embed-text")
    provider.client = _Client()
    result = provider.embed(["a", "b"])
    assert len(result.vectors) == 2
    assert provider.client.calls == 2
