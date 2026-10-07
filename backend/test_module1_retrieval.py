import asyncio

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.document_chunk import DocumentChunk


async def main():
    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(DocumentChunk)
            .where(
                DocumentChunk.section_title.ilike("%MODULE 1%")
            )
            .limit(10)
        )

        chunks = result.scalars().all()

        print(f"Found {len(chunks)} chunks")

        for chunk in chunks:
            print("\n" + "-" * 60)
            print(f"Chunk ID: {chunk.id}")
            print(f"Document ID: {chunk.document_id}")
            print(f"Section: {chunk.section_title}")
            print(f"Content: {chunk.content[:300]}")


if __name__ == "__main__":
    asyncio.run(main())