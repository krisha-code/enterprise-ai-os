from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.services.embedding_service import EmbeddingService
from app.services.reranker_service import RerankerService

class HybridSearchService:

    @staticmethod
    def rrf_score(
        rank: int,
        k: int = 60,
    ) -> float:
        return 1 / (k + rank)

    @staticmethod
    async def search(
        db: AsyncSession,
        query: str,
        user_id: int,
        limit: int = 20,
        max_distance: float | None =None,
    ):
        # ----------------------------------------
        # Generate query embedding
        # ----------------------------------------

        query_embedding = (
            EmbeddingService.generate_embedding(query)
        )

        # ----------------------------------------
        # Vector retrieval
        # ----------------------------------------

        vector_results = (
            await DocumentChunkRepository.similarity_search_with_scores(
                db=db,
                query_embedding=query_embedding,
                user_id=user_id,
                limit=limit,
                max_distance=max_distance,
            )
        )

        # ----------------------------------------
        # Keyword retrieval
        # ----------------------------------------

        keyword_results = (
            await DocumentChunkRepository.keyword_search(
                db=db,
                query_text=query,
                user_id=user_id,
                limit=limit,
            )
        )

        # ----------------------------------------
        # RRF score aggregation
        # ----------------------------------------

        scores = {}
        chunks = {}

        # Vector ranking
        for rank, (chunk, distance) in enumerate(
            vector_results,
            start=1,
        ):
            scores[chunk.id] = (
                scores.get(chunk.id, 0)
                + HybridSearchService.rrf_score(rank)
            )

            chunks[chunk.id] = chunk

        # Keyword ranking
        for rank, (chunk, keyword_score) in enumerate(
            keyword_results,
            start=1,
        ):
            scores[chunk.id] = (
                scores.get(chunk.id, 0)
                + HybridSearchService.rrf_score(rank)
            )

            chunks[chunk.id] = chunk

        # ----------------------------------------
        # Combine and rank
        # ----------------------------------------

        ranked_chunks = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        return [
            (chunks[chunk_id], score)
            for chunk_id, score in ranked_chunks[:limit]
        ]   


    @staticmethod
    async def debug_search(
        db: AsyncSession,
        query: str,
        user_id: int,
        candidate_limit: int = 20,
        max_distance: float | None = None,
    ):
        query_embedding = (
            EmbeddingService.generate_embedding(query)
        )

        vector_results = (
            await DocumentChunkRepository.similarity_search_with_scores(
                db=db,
                query_embedding=query_embedding,
                user_id=user_id,
                limit=candidate_limit,
                max_distance=max_distance,
            )
        )

        keyword_results = (
            await DocumentChunkRepository.keyword_search(
                db=db,
                query_text=query,
                user_id=user_id,
                limit=candidate_limit,
            )
        )

        scores = {}
        chunks = {}

        vector_ranks = {}
        keyword_ranks = {}

        # ----------------------------------------
        # Vector results
        # ----------------------------------------

        for rank, (chunk, distance) in enumerate(
            vector_results,
            start=1,
        ):
            vector_ranks[chunk.id] = {
                "rank": rank,
                "distance": float(distance),
            }

            scores[chunk.id] = (
                scores.get(chunk.id, 0)
                + HybridSearchService.rrf_score(rank)
            )

            chunks[chunk.id] = chunk

        # ----------------------------------------
        # Keyword results
        # ----------------------------------------

        for rank, (chunk, keyword_score) in enumerate(
            keyword_results,
            start=1,
        ):
            keyword_ranks[chunk.id] = {
                "rank": rank,
                "score": float(keyword_score),
            }

            scores[chunk.id] = (
                scores.get(chunk.id, 0)
                + HybridSearchService.rrf_score(rank)
            )

            chunks[chunk.id] = chunk

        # ----------------------------------------
        # RRF ranking
        # ----------------------------------------

        ranked_chunks = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        candidates = []

        for rrf_rank, (chunk_id, rrf_score) in enumerate(
            ranked_chunks,
            start=1,
        ):
            candidates.append(
                {
                    "chunk": chunks[chunk_id],
                    "rrf_rank": rrf_rank,
                    "rrf_score": rrf_score,
                    "vector": vector_ranks.get(chunk_id),
                    "keyword": keyword_ranks.get(chunk_id),
                }
            )

        # ----------------------------------------
        # Cross-Encoder reranking
        # ----------------------------------------

        reranker_input = [
            candidate["chunk"]
            for candidate in candidates
        ]
        reranked_results = RerankerService.rerank(
            question=query,
            chunks=reranker_input,
        )

        reranker_scores = {
            chunk.id: float(score)
            for chunk, score in reranked_results
        }

        # ----------------------------------------
        # Final debug output
        # ----------------------------------------

        debug_results = []

        for final_rank, (chunk, reranker_score) in enumerate(
            reranked_results,
            start=1,
        ):
            matching_candidate = next(
                candidate
                for candidate in candidates
                if candidate["chunk"].id == chunk.id
            )

            debug_results.append(
                {
                    "final_rank": final_rank,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "rrf_rank": matching_candidate["rrf_rank"],
                    "rrf_score": matching_candidate["rrf_score"],
                    "vector": matching_candidate["vector"],
                    "keyword": matching_candidate["keyword"],
                    "reranker_score": float(reranker_score),
                    "content": chunk.content,
                }
            )

        return debug_results