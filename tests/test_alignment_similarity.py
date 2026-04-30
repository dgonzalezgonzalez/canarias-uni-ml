from src.canarias_uni_ml.alignment.similarity import cosine_similarity


def test_cosine_similarity_range_and_value():
    assert round(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 4) == 1.0
    assert round(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 4) == 0.0
    assert cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0
