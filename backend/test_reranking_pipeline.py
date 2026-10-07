import asyncio

from app.database.session import AsyncSessionLocal
from app.services.hybrid_search_service import (
    HybridSearchService,
)
from app.services.reranker_service import (
    RerankerService,
)


async def main():

    question = "Who approves an employee's leave request?"

    async with AsyncSessionLocal() as db:

        hybrid_results = (
            await HybridSearchService.search(
                db=db,
                query=question,
                user_id=1,
                limit=5,
            )
        )

    print("\n===== HYBRID RESULTS =====")

    for rank, (chunk, rrf_score) in enumerate(
        hybrid_results,
        start=1,
    ):

        print(
            f"\nRank {rank}"
        )

        print(
            f"Chunk ID: {chunk.id}"
        )

        print(
            f"RRF Score: {rrf_score:.6f}"
        )

        print(
            f"Content: {chunk.content}"
        )

    chunks = [
        chunk
        for chunk, rrf_score in hybrid_results
    ]

    reranked_results = (
        RerankerService.rerank(
            question=question,
            chunks=chunks,
        )
    )

    print("\n===== RERANKED RESULTS =====")

    for rank, (chunk, score) in enumerate(
        reranked_results,
        start=1,
    ):

        print(
            f"\nRank {rank}"
        )

        print(
            f"Chunk ID: {chunk.id}"
        )

        print(
            f"Cross-Encoder Score: {score:.6f}"
        )

        print(
            f"Content: {chunk.content}"
        )


if __name__ == "__main__":
    asyncio.run(main())