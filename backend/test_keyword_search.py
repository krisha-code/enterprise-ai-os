import asyncio

from app.database.session import AsyncSessionLocal
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)


async def main():

    query = "transportation allowance"

    async with AsyncSessionLocal() as db:

        results = await (
            DocumentChunkRepository.keyword_search(
                db=db,
                query_text=query,
                organization_id=1,
                limit=5,
            )
        )

    print("\n===== QUERY =====")
    print(query)

    print("\n===== KEYWORD RESULTS =====")

    for rank, (chunk, score) in enumerate(
        results,
        start=1,
    ):

        print(f"\n--- Rank {rank} ---")
        print(f"Chunk ID: {chunk.id}")
        print(f"Document ID: {chunk.document_id}")
        print(f"Keyword Score: {score:.6f}")

        print("Content:")
        print(chunk.content)


if __name__ == "__main__":
    asyncio.run(main())
