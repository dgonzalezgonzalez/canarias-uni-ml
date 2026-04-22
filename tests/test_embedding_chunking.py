from src.canarias_uni_ml.embeddings.chunking import chunk_text


def test_chunk_text_splits_long_input():
    text = "a" * 6500
    chunks = chunk_text(text, max_chars=3000)
    assert len(chunks) == 3
    assert all(len(chunk) <= 3000 for chunk in chunks[:2])
