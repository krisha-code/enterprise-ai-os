from app.services.hybrid_search_service import HybridSearchService
from app.services.reranker_service import RerankerService


class DocumentSearchService:

    @staticmethod
    async def search_with_scores(
        db,
        query,
        user_id,
        limit=5,
        max_distance=None,
    ):
        candidate_limit = max(limit * 4, 20)

        hybrid_results = await HybridSearchService.search(
            db=db,
            query=query,
            user_id=user_id,
            limit=candidate_limit,
            max_distance=max_distance,
        )

        if not hybrid_results:
            return []

        chunks = [
            chunk
            for chunk, score in hybrid_results
        ]

        reranked_results = RerankerService.rerank(
            question=query,
            chunks=chunks,
        )

        return reranked_results[:limit]

    @staticmethod
    async def search(
        db,
        query,
        user_id,
        limit=5,
        max_distance=None,
    ):
        reranked_results = (
            await DocumentSearchService.search_with_scores(
                db=db,
                query=query,
                user_id=user_id,
                limit=limit,
                max_distance=max_distance,
            )
        )

        return [
            chunk
            for chunk, score in reranked_results
        ]