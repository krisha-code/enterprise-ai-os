import asyncio

from app.services.prompt_builder import PromptBuilder
from app.services.llm_service import LLMService


async def main():

    context = """
Enterprise employees receive 20 days of annual leave every year.

Employees must submit leave requests to their manager before taking leave.

Managers are responsible for reviewing and approving leave requests.
""".strip()

    question = "How many days of annual leave do employees receive?"

    prompt = PromptBuilder.build(
        context=context,
        question=question,
    )

    print("===== GENERATED PROMPT =====")
    print(prompt)

    answer = await LLMService.generate(prompt)

    print("\n===== LLM ANSWER =====")
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())