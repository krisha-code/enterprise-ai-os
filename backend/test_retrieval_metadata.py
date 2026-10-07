import asyncio

from app.database.session import AsyncSessionLocal
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.services.embedding_service import EmbeddingService


async def main():

    query = "What is a UAV?"

    # ----------------------------------------
    # Generate query embedding
    # ----------------------------------------

    query_embedding = EmbeddingService.generate_embedding(
        query
    )

    # ----------------------------------------
    # Search database
    # ----------------------------------------

    async with AsyncSessionLocal() as db:

        results = (
            await DocumentChunkRepository
            .similarity_search_with_scores(
                db=db,
                query_embedding=query_embedding,
                user_id=1,
                limit=5,
                max_distance=0.55,
            )
        )

        # ----------------------------------------
        # Display results
        # ----------------------------------------

        print("\n--- RETRIEVAL METADATA ---")

        for chunk, distance in results:

            print("\n" + "-" * 60)

            print(f"Chunk ID: {chunk.id}")
            print(f"Distance: {distance}")
            print(f"Document ID: {chunk.document_id}")
            print(f"Filename: {chunk.document.filename}")
            print(f"Section: {chunk.section_title}")
            print(f"Page: {chunk.page_number}")
            print(f"Content: {chunk.content[:200]}")


if __name__ == "__main__":
    asyncio.run(main())