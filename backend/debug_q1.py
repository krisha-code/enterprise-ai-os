import asyncio

from app.database.session import AsyncSessionLocal
from app.services.embedding_service import EmbeddingService
from app.repositories.document_chunk_repository import DocumentChunkRepository


USER_ID = 1
QUESTION = "What is covered in MODULE 1?"


async def main():
    async with AsyncSessionLocal() as db:

        query_embedding = EmbeddingService.generate_embedding(
            QUESTION
        )

        results = await DocumentChunkRepository.similarity_search_with_scores(
            db=db,
            query_embedding=query_embedding,
            user_id=USER_ID,
            limit=20,
            max_distance=None,
        )

        print("\nQ1 VECTOR DIAGNOSTIC")
        print("=" * 80)

        if not results:
            print("NO VECTOR RESULTS")
            return

        for rank, (chunk, distance) in enumerate(
            results,
            start=1,
        ):
            section = (
                chunk.section_title
                if chunk.section_title
                else "Unknown section"
            )

            print(
                f"RANK {rank} | "
                f"distance={float(distance):.6f} | "
                f"chunk_id={chunk.id} | "
                f"section={section}"
            )


if __name__ == "__main__":
    asyncio.run(main())