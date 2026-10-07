import asyncio

from app.database.session import AsyncSessionLocal
from app.services.rag_service import RAGService


async def main():

    question = "What is a UAV?"

    async with AsyncSessionLocal() as db:

        result = await RAGService.answer(
            db=db,
            question=question,
            user_id=1,
            limit=3,
        )

        print("\n--- ANSWER ---")
        print(result.answer)

        print("\n--- CITATIONS ---")

        for citation in result.citations:

            print("\n" + "-" * 60)
            print(f"Source ID: {citation.source_id}")
            print(f"Document: {citation.filename}")
            print(f"Section: {citation.section_title}")
            print(f"Page: {citation.page_number}")
            print(f"Chunk ID: {citation.chunk_id}")


if __name__ == "__main__":
    asyncio.run(main())