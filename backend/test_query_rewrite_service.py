
from app.services.query_rewrite_service import QueryRewriteService


def test_standalone_question_is_preserved():
    question = "What is a multi-rotor UAV?"

    result = QueryRewriteService.rewrite(
        question=question,
        conversation_history="No previous conversation.",
    )

    assert result == question


def test_empty_question_is_preserved_as_empty():
    result = QueryRewriteService.rewrite(
        question="   ",
        conversation_history="No previous conversation.",
    )

    assert result == ""


def test_rewrites_its_advantages():
    result = QueryRewriteService.rewrite(
        question="What are its advantages?",
        conversation_history=(
            "User: What is a multi-rotor UAV?\n"
            "Assistant: A multi-rotor UAV uses multiple rotors."
        ),
    )

    assert result == "What are the advantages of multi-rotor UAV?"


def test_rewrites_its_disadvantages():
    result = QueryRewriteService.rewrite(
        question="What are its disadvantages?",
        conversation_history=(
            "User: Explain fixed-wing UAVs."
        ),
    )

    assert result == "What are the disadvantages of fixed-wing UAV?"


def test_unknown_follow_up_is_preserved():
    question = "Can you explain that further?"

    result = QueryRewriteService.rewrite(
        question=question,
        conversation_history=(
            "User: What is a multi-rotor UAV?"
        ),
    )

    assert result == question

def test_rewrites_their_advantages():
    result = QueryRewriteService.rewrite(
        question="What are their advantages?",
        conversation_history=(
            "User: Explain fixed-wing UAVs."
        ),
    )

    assert result == "What are the advantages of fixed-wing UAVs?"


def test_uses_most_recently_mentioned_uav_type():
    result = QueryRewriteService.rewrite(
        question="What are its advantages?",
        conversation_history=(
            "User: Explain multi-rotor UAVs.\n"
            "Assistant: Multi-rotor UAVs use multiple rotors.\n"
            "User: Now explain fixed-wing UAV."
        ),
    )

    assert result == "What are the advantages of fixed-wing UAV?"
