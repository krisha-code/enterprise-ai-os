import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.services.hybrid_search_service import HybridSearchService


def test_search_combines_vector_and_keyword_results():
    async def run_test():
        chunk_a = SimpleNamespace(id=1, content="Vector result")
        chunk_b = SimpleNamespace(id=2, content="Keyword result")
        chunk_c = SimpleNamespace(id=3, content="Shared result")

        vector_results = [
            (chunk_a, 0.10),
            (chunk_c, 0.20),
        ]
        keyword_results = [
            (chunk_b, 0.90),
            (chunk_c, 0.80),
        ]

        with (
            patch(
                "app.services.hybrid_search_service.EmbeddingService.generate_embedding",
                return_value=[0.1, 0.2],
            ),
            patch(
                "app.services.hybrid_search_service.DocumentChunkRepository.similarity_search_with_scores",
                new_callable=AsyncMock,
                return_value=vector_results,
            ),
            patch(
                "app.services.hybrid_search_service.DocumentChunkRepository.keyword_search",
                new_callable=AsyncMock,
                return_value=keyword_results,
            ),
        ):
            results = await HybridSearchService.search(
                db=object(),
                query="test query",
                user_id=7,
                limit=5,
            )

        result_ids = [chunk.id for chunk, _ in results]

        assert set(result_ids) == {1, 2, 3}
        assert len(result_ids) == 3
        assert result_ids[0] == 3
        assert results[0][1] == pytest.approx(
            HybridSearchService.rrf_score(2)
            + HybridSearchService.rrf_score(2)
        )

    asyncio.run(run_test())


def test_search_limits_number_of_results():
    async def run_test():
        chunks = [
            SimpleNamespace(id=index, content=f"Chunk {index}")
            for index in range(1, 4)
        ]

        with (
            patch(
                "app.services.hybrid_search_service.EmbeddingService.generate_embedding",
                return_value=[0.1, 0.2],
            ),
            patch(
                "app.services.hybrid_search_service.DocumentChunkRepository.similarity_search_with_scores",
                new_callable=AsyncMock,
                return_value=[(chunk, 0.1) for chunk in chunks],
            ),
            patch(
                "app.services.hybrid_search_service.DocumentChunkRepository.keyword_search",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            results = await HybridSearchService.search(
                db=object(),
                query="test query",
                user_id=7,
                limit=2,
            )

        assert len(results) == 2

    asyncio.run(run_test())
