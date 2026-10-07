import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.session import AsyncSessionLocal
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import EmbeddingService
from app.services.context_builder import ContextBuilder


async def main():

    question = "What is a UAV?"

    query_embedding = EmbeddingService.generate_embedding(
        question
    )

    async with AsyncSessionLocal() as db:

        distance = DocumentChunk.embedding.cosine_distance(
            query_embedding
        )

        result = await db.execute(
            select(DocumentChunk)
            .options(
                selectinload(DocumentChunk.document)
            )
            .where(
                DocumentChunk.document_id == 4,
                DocumentChunk.embedding.is_not(None),
            )
            .order_by(distance)
            .limit(3)
        )

        chunks = result.scalars().all()

        print("\n--- RETRIEVED SOURCES ---")

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):

            print("\n" + "-" * 60)
            print(f"Source ID: {index}")
            print(f"Chunk ID: {chunk.id}")
            print(f"Document: {chunk.document.filename}")
            print(f"Section: {chunk.section_title}")
            print(f"Page: {chunk.page_number}")
            print(f"Content: {chunk.content[:200]}")

        # ----------------------------------------
        # Build citation-ready context
        # ----------------------------------------

        context = ContextBuilder.build(chunks)

        print("\n")
        print("=" * 60)
        print("--- CITATION CONTEXT ---")
        print(context)


if __name__ == "__main__":
    asyncio.run(main())