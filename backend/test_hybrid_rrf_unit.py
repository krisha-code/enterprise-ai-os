import pytest

from app.services.hybrid_search_service import HybridSearchService


def test_rrf_score_uses_expected_formula():
    assert HybridSearchService.rrf_score(1) == pytest.approx(1 / 61)


def test_rrf_score_decreases_as_rank_worsens():
    assert (
        HybridSearchService.rrf_score(1)
        > HybridSearchService.rrf_score(2)
        > HybridSearchService.rrf_score(3)
    )


def test_rrf_score_respects_custom_k():
    assert HybridSearchService.rrf_score(1, k=10) == pytest.approx(1 / 11)


def test_rrf_score_is_positive_for_positive_rank():
    assert HybridSearchService.rrf_score(5) > 0
