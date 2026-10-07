import asyncio

from app.database.session import AsyncSessionLocal
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.services.embedding_service import EmbeddingService


async def main():

    question = "What is covered in MODULE 1?"

    async with AsyncSessionLocal() as db:

        print("\n" + "=" * 70)
        print("KEYWORD SEARCH")
        print("=" * 70)

        keyword_results = await DocumentChunkRepository.keyword_search(
            db=db,
            query_text=question,
            user_id=1,
            limit=10,
        )

        print(f"Keyword results: {len(keyword_results)}")

        for rank, (chunk, score) in enumerate(
            keyword_results,
            start=1,
        ):
            print("\n" + "-" * 60)
            print(f"Rank: {rank}")
            print(f"Chunk ID: {chunk.id}")
            print(f"Document ID: {chunk.document_id}")
            print(f"Score: {score}")
            print(f"Section: {chunk.section_title}")
            print(f"Content: {chunk.content[:250]}")

        print("\n" + "=" * 70)
        print("VECTOR SEARCH")
        print("=" * 70)

        query_embedding = EmbeddingService.generate_embedding(
            question
        )

        vector_results = (
            await DocumentChunkRepository.similarity_search_with_scores(
                db=db,
                query_embedding=query_embedding,
                user_id=1,
                limit=10,
                max_distance=0.55,
            )
        )

        print(f"Vector results: {len(vector_results)}")

        for rank, (chunk, distance) in enumerate(
            vector_results,
            start=1,
        ):
            print("\n" + "-" * 60)
            print(f"Rank: {rank}")
            print(f"Chunk ID: {chunk.id}")
            print(f"Document ID: {chunk.document_id}")
            print(f"Distance: {distance}")
            print(f"Section: {chunk.section_title}")
            print(f"Content: {chunk.content[:250]}")


if __name__ == "__main__":
    asyncio.run(main())