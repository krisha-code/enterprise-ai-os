import asyncio

from app.database.session import AsyncSessionLocal
from app.services.hybrid_search_service import HybridSearchService


async def main():
    query = "What is crop health detection?"

    async with AsyncSessionLocal() as db:
        results = await HybridSearchService.debug_search(
            db=db,
            query=query,
            user_id=1,
            candidate_limit=20,
        )

        for result in results[:10]:
            print("\n" + "=" * 80)
            print(f"Final rank:     {result['final_rank']}")
            print(f"Chunk ID:       {result['chunk_id']}")
            print(f"Chunk index:    {result['chunk_index']}")
            print(f"RRF rank:       {result['rrf_rank']}")
            print(f"RRF score:      {result['rrf_score']}")
            print(f"Vector:         {result['vector']}")
            print(f"Keyword:        {result['keyword']}")
            print(f"Reranker score: {result['reranker_score']}")
            print(f"Content:\n{result['content']}")


if __name__ == "__main__":
    asyncio.run(main())