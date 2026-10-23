import asyncio

from app.database.session import AsyncSessionLocal
from app.services.hybrid_search_service import (
    HybridSearchService,
)


async def main():

    query = "transportation allowance?"

    async with AsyncSessionLocal() as db:

        results = await HybridSearchService.search(
            db=db,
            query=query,
            organization_id=1,
            limit=5,
        )

    print("\n===== QUERY =====")
    print(query)

    print("\n===== HYBRID RESULTS =====")

    for rank, (chunk, score) in enumerate(
        results,
        start=1,
    ):
        print(f"\n--- Rank {rank} ---")
        print(f"Chunk ID: {chunk.id}")
        print(f"Document ID: {chunk.document_id}")
        print(f"RRF Score: {score:.6f}")

        print("Content:")
        print(chunk.content)


if __name__ == "__main__":
    asyncio.run(main())
