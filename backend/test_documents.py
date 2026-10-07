import asyncio

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.document import Document


async def main():

    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(Document)
            .order_by(Document.id)
        )

        documents = result.scalars().all()

        print("\n--- DOCUMENTS ---")

        for document in documents:

            print("\n" + "-" * 60)
            print(f"ID: {document.id}")
            print(f"Filename: {document.filename}")
            print(f"User ID: {document.user_id}")
            print(f"Content type: {document.content_type}")
            print(f"Created: {document.created_at}")


if __name__ == "__main__":
    asyncio.run(main())