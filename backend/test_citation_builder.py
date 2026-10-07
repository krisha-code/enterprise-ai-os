import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.session import AsyncSessionLocal
from app.models.document_chunk import DocumentChunk
from app.services.citation_builder import CitationBuilder


async def main():

    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(DocumentChunk)
            .options(
                selectinload(DocumentChunk.document)
            )
            .where(
                DocumentChunk.document_id == 4
            )
            .order_by(
                DocumentChunk.chunk_index
            )
            .limit(3)
        )

        chunks = result.scalars().all()

        citations = CitationBuilder.build(chunks)

        print("\n--- CITATIONS ---")

        for citation in citations:

            print("\n" + "-" * 60)
            print(f"Source ID: {citation.source_id}")
            print(f"Document ID: {citation.document_id}")
            print(f"Chunk ID: {citation.chunk_id}")
            print(f"Filename: {citation.filename}")
            print(f"Section: {citation.section_title}")
            print(f"Page: {citation.page_number}")


if __name__ == "__main__":
    asyncio.run(main())