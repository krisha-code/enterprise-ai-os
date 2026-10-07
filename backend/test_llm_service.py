import asyncio

from app.services.llm_service import LLMService


async def main():
    answer = await LLMService.generate(
        "Explain what RAG is in one simple sentence."
    )

    print("LLM Answer:")
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())