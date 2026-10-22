
from app.services.answer_validation_service import AnswerValidationService


def test_empty_answer_is_rejected():
    assert not AnswerValidationService.validate(
        answer="",
        context="A fixed-wing UAV cannot hover.",
        question="What are its limitations?",
    )


def test_answer_with_no_context_overlap_is_rejected():
    assert not AnswerValidationService.validate(
        answer="Bananas contain potassium and fiber.",
        context="A fixed-wing UAV cannot hover.",
        question="What are its limitations?",
    )


def test_supported_answer_passes():
    assert AnswerValidationService.validate(
        answer="A fixed-wing UAV cannot hover.",
        context=(
            "A fixed-wing UAV looks like a small airplane. "
            "Disadvantages: Cannot hover."
        ),
        question="What are its limitations?",
    )


def test_contradictory_hover_claim_is_rejected():
    assert not AnswerValidationService.validate(
        answer="A fixed-wing UAV can hover.",
        context="A fixed-wing UAV cannot hover.",
        question="What are its limitations?",
    )


def test_disadvantage_is_not_accepted_as_an_advantage():
    assert not AnswerValidationService.validate(
        answer="One advantage is that it requires more operating skill.",
        context=(
            "Advantages: Long flight duration. "
            "Disadvantages: Cannot hover. Requires more operating skill."
        ),
        question="What are its advantages?",
    )


    
def test_extract_labeled_advantages_excludes_disadvantages():
    context = (
        "Advantages: Long flight duration, often one or several hours. "
        "Covers large areas quickly. More energy-efficient. "
        "Suitable for large-area mapping and surveying. "
        "Disadvantages: Cannot hover. Requires more operating skill."
    )

    result = AnswerValidationService.extract_labeled_section(
        context=context,
        label="Advantages",
    )

    assert result is not None
    assert "Long flight duration" in result
    assert "Covers large areas quickly" in result
    assert "More energy-efficient" in result
    assert "mapping and surveying" in result
    assert "Cannot hover" not in result
    assert "Requires more operating skill" not in result


def test_extract_labeled_disadvantages_excludes_advantages():
    context = (
        "Advantages: Long flight duration. "
        "Disadvantages: Cannot hover. "
        "Requires more operating skill."
    )

    result = AnswerValidationService.extract_labeled_section(
        context=context,
        label="Disadvantages",
    )

    assert result is not None
    assert "Cannot hover" in result
    assert "Requires more operating skill" in result
    assert "Long flight duration" not in result
