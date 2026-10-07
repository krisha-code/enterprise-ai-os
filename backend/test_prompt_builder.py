from app.services.prompt_builder import PromptBuilder


def main():

    context = """
[Source 1]
Document: Q1.docx
Section: MODULE 1 – FUNDAMENTALS OF DRONE TECHNOLOGY
Page: N/A
Content:
A UAV is an aircraft that flies without a human pilot.

[Source 2]
Document: Q1.docx
Section: MODULE 1 – FUNDAMENTALS OF DRONE TECHNOLOGY
Page: N/A
Content:
UAVs can be controlled remotely or operate automatically.
""".strip()

    question = "What is a UAV?"

    prompt = PromptBuilder.build(
        context=context,
        question=question,
    )

    print("\n--- GENERATED PROMPT ---")
    print(prompt)


if __name__ == "__main__":
    main()