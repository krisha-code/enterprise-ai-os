from types import SimpleNamespace
from unittest.mock import patch

from app.services.reranker_service import RerankerService


def test_rerank_orders_chunks_by_model_score():
    question = "Who approves an employee's leave request?"

    chunks = [
        SimpleNamespace(
            content="Employees receive 20 days of annual leave.",
            section_title="Leave Policy",
        ),
        SimpleNamespace(
            content="Managers approve leave requests.",
            section_title="Leave Policy",
        ),
        SimpleNamespace(
            content="Employees can contact HR with questions.",
            section_title="HR Policy",
        ),
    ]

    with patch.object(
        RerankerService.model,
        "predict",
        return_value=[0.1, 0.9, 0.2],
    ):
        results = RerankerService.rerank(
            question=question,
            chunks=chunks,
        )

    assert [chunk.content for chunk, _ in results] == [
        "Managers approve leave requests.",
        "Employees can contact HR with questions.",
        "Employees receive 20 days of annual leave.",
    ]
    assert [float(score) for _, score in results] == [
        0.9,
        0.2,
        0.1,
    ]
