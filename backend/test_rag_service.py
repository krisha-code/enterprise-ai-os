import asyncio

from app.database.session import AsyncSessionLocal
from app.services.rag_service import RAGService


async def main():
    question = "Who approves an employee's leave request?"
    async with AsyncSessionLocal() as db:

        answer = await RAGService.answer(
            db=db,
            question=question,
            user_id=1,
            limit=5,
        )

    print("\n===== RAG ANSWER =====")
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())