import asyncio

from app.database.session import AsyncSessionLocal
from app.services.document_search_service import DocumentSearchService
from app.services.context_builder import ContextBuilder
from app.services.prompt_builder import PromptBuilder
from app.services.llm_service import LLMService


async def main():

    question = "What is a UAV?"

    async with AsyncSessionLocal() as db:

        # ----------------------------------------
        # Retrieve relevant chunks
        # ----------------------------------------

        chunks = await DocumentSearchService.search(
            db=db,
            query=question,
            organization_id=1,
            limit=3,
            max_distance=0.55,
        )

        if not chunks:
            print("No relevant chunks found.")
            return

        # ----------------------------------------
        # Build source-aware context
        # ----------------------------------------

        context = ContextBuilder.build(chunks)

        print("\n--- CONTEXT ---")
        print(context)

        # ----------------------------------------
        # Build prompt
        # ----------------------------------------

        prompt = PromptBuilder.build(
            context=context,
            question=question,
        )

        print("\n--- PROMPT ---")
        print(prompt)

        # ----------------------------------------
        # Generate answer
        # ----------------------------------------

        answer = await LLMService.generate(prompt)

        print("\n--- ANSWER ---")
        print(answer)


if __name__ == "__main__":
    asyncio.run(main())
