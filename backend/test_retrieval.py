import asyncio

from app.database.session import AsyncSessionLocal
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.services.embedding_service import EmbeddingService


async def main():

    question = "How many days of annual leave do employees receive?"

    query_embedding = EmbeddingService.generate_embedding(
        question
    )

    async with AsyncSessionLocal() as db:

        results = await (
            DocumentChunkRepository.similarity_search_with_scores(
                db=db,
                query_embedding=query_embedding,
                organization_id=1,
                limit=5,
                max_distance=0.55,
            )
        )

    print("\n===== QUERY =====")
    print(question)

    print("\n===== RETRIEVED CHUNKS =====")

    for rank, (chunk, distance) in enumerate(
        results,
        start=1,
    ):

        print(f"\n--- Rank {rank} ---")
        print(f"Chunk ID: {chunk.id}")
        print(f"Document ID: {chunk.document_id}")
        print(f"Chunk Index: {chunk.chunk_index}")
        print(f"Cosine Distance: {distance:.6f}")

        print("Content:")
        print(chunk.content)


if __name__ == "__main__":
    asyncio.run(main())
