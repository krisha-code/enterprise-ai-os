import asyncio

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.document_chunk import DocumentChunk


async def main():

    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.section_title.is_not(None))
            .order_by(
                DocumentChunk.document_id,
                DocumentChunk.chunk_index,
            )
            .limit(10)
        )

        chunks = result.scalars().all()

        print("\n--- DATABASE METADATA ---")

        for chunk in chunks:

            print("\n" + "-" * 60)
            print(f"Chunk ID: {chunk.id}")
            print(f"Document ID: {chunk.document_id}")
            print(f"Chunk index: {chunk.chunk_index}")
            print(f"Section: {chunk.section_title}")
            print(f"Page: {chunk.page_number}")
            print(f"Content: {chunk.content[:200]}")


if __name__ == "__main__":
    asyncio.run(main())