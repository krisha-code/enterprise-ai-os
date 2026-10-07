import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.session import AsyncSessionLocal
from app.models.document_chunk import DocumentChunk
from app.services.context_builder import ContextBuilder


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

        context = ContextBuilder.build(chunks)

        print("\n--- GENERATED CONTEXT ---")
        print(context)


if __name__ == "__main__":
    asyncio.run(main())