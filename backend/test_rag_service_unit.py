import asyncio
from unittest.mock import AsyncMock, patch

from app.services.rag_service import RAGService
from app.schemas.citation import Citation


def test_no_retrieval_results_returns_insufficient_evidence():
    async def run_test():
        with patch(
            "app.services.rag_service.DocumentSearchService.search_with_scores",
            new_callable=AsyncMock,
            return_value=[],
        ) as search, patch(
            "app.services.rag_service.LLMService.generate",
            new_callable=AsyncMock,
        ) as generate:
            response = await RAGService.answer(
                db=None,
                question="Who approves leave?",
                organization_id=1,
            )

        assert response.answer == RAGService.INSUFFICIENT_EVIDENCE_MESSAGE
        assert response.citations == []
        search.assert_awaited_once_with(
            db=None,
            query="Who approves leave?",
            organization_id=1,
            limit=5,
            max_distance=None,
        )
        generate.assert_not_awaited()

    asyncio.run(run_test())


def test_insufficient_evidence_does_not_call_llm():
    async def run_test():
        fake_results = [(object(), 0.1)]

        with patch(
            "app.services.rag_service.DocumentSearchService.search_with_scores",
            new_callable=AsyncMock,
            return_value=fake_results,
        ), patch(
            "app.services.rag_service.EvidenceSufficiencyService.evaluate",
            return_value=False,
        ), patch(
            "app.services.rag_service.LLMService.generate",
            new_callable=AsyncMock,
        ) as generate:
            response = await RAGService.answer(
                db=None,
                question="Who approves leave?",
                organization_id=1,
            )

        assert response.answer == RAGService.INSUFFICIENT_EVIDENCE_MESSAGE
        assert response.citations == []
        generate.assert_not_awaited()

    asyncio.run(run_test())


def test_sufficient_evidence_generates_answer_and_citations():
    async def run_test():
        fake_chunk = object()
        fake_results = [(fake_chunk, 0.1)]
        fake_citations = [Citation(source_id=1, document_id=10, chunk_id=100, filename="policy.pdf")]

        with patch(
            "app.services.rag_service.DocumentSearchService.search_with_scores",
            new_callable=AsyncMock,
            return_value=fake_results,
        ), patch(
            "app.services.rag_service.EvidenceSufficiencyService.evaluate",
            return_value=True,
        ), patch(
            "app.services.rag_service.ContextBuilder.build",
            return_value="Retrieved context",
        ) as build_context, patch(
            "app.services.rag_service.PromptBuilder.build",
            return_value="Generated prompt",
        ) as build_prompt, patch(
            "app.services.rag_service.LLMService.generate",
            new_callable=AsyncMock,
            return_value="The manager approves leave.",
        ) as generate, patch(
            "app.services.rag_service.AnswerValidationService.validate",
            return_value=True,
        ), patch(
            "app.services.rag_service.CitationBuilder.build_relevant",
            return_value=fake_citations,
        ) as build_citations:
            response = await RAGService.answer(
                db=None,
                question="Who approves leave?",
                organization_id=1,
            )

        assert response.answer == "The manager approves leave."
        assert response.citations == fake_citations
        build_context.assert_called_once_with([fake_chunk])
        build_prompt.assert_called_once_with(
            context="Retrieved context",
            question="Who approves leave?",
        )
        generate.assert_awaited_once_with("Generated prompt")
        build_citations.assert_called_once_with(
            chunks=[fake_chunk],
            answer="The manager approves leave.",
            question="Who approves leave?",
        )

    asyncio.run(run_test())

