from app.services.prompt_builder import PromptBuilder


def test_prompt_includes_question_and_retrieved_context():
    context = "[Source 1]\nContent:\nA UAV is an unmanned aircraft."
    prompt = PromptBuilder.build(
        context=context,
        question="What is a UAV?",
    )

    assert "USER QUESTION:" in prompt
    assert "What is a UAV?" in prompt
    assert "RETRIEVED CONTEXT:" in prompt
    assert context in prompt


def test_prompt_includes_evidence_and_citation_instructions():
    prompt = PromptBuilder.build(
        context="[Source 1]\nContent:\nA UAV is an unmanned aircraft.",
        question="What is a UAV?",
    )

    assert "Use the provided context as the only source of factual evidence." in prompt
    assert "Every factual claim in the answer must be supported by the context." in prompt
    assert "Use only source identifiers that actually appear in the context." in prompt


def test_prompt_uses_default_when_history_is_empty():
    prompt = PromptBuilder.build(
        context="Sample context.",
        question="  What is a UAV?  ",
        conversation_history="  ",
    )

    assert "No previous conversation." in prompt
    assert prompt.endswith("What is a UAV?")


def test_prompt_includes_trimmed_conversation_history():
    prompt = PromptBuilder.build(
        context="Sample context.",
        question="What is it?",
        conversation_history="  User: Tell me about UAVs.  ",
    )

    assert "User: Tell me about UAVs." in prompt
    assert "  User: Tell me about UAVs.  " not in prompt
