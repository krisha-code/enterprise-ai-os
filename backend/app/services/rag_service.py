from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.rag import RAGResponse
from app.services.citation_builder import CitationBuilder
from app.services.context_builder import ContextBuilder
from app.services.document_search_service import DocumentSearchService
from app.services.evidence_sufficiency_service import (
    EvidenceSufficiencyService,
)
from app.services.llm_service import LLMService
from app.services.prompt_builder import PromptBuilder


class RAGService:
    INSUFFICIENT_EVIDENCE_MESSAGE = (
        "I don't have enough information to answer that question."
    )

    @staticmethod
    async def answer(
        db: AsyncSession,
        question: str,
        user_id: int,
        limit: int = 5,
    ) -> RAGResponse:

        # --------------------------------------------------
        # Step 1: Retrieve and rerank evidence
        # --------------------------------------------------

        reranked_results = (
            await DocumentSearchService.search_with_scores(
                db=db,
                query=question,
                user_id=user_id,
                limit=limit,
                max_distance=None,
            )
        )

        # --------------------------------------------------
        # Step 2: No retrieval results
        # --------------------------------------------------

        if not reranked_results:
            return RAGResponse(
                answer=RAGService.INSUFFICIENT_EVIDENCE_MESSAGE,
                citations=[],
            )

        # --------------------------------------------------
        # Step 3: Evaluate evidence sufficiency
        # --------------------------------------------------

        evidence_sufficient = (
            EvidenceSufficiencyService.evaluate(
                reranked_results
            )
        )

        # --------------------------------------------------
        # Step 4: Stop if evidence is insufficient
        # --------------------------------------------------

        if not evidence_sufficient:
            return RAGResponse(
                answer=RAGService.INSUFFICIENT_EVIDENCE_MESSAGE,
                citations=[],
            )

        # --------------------------------------------------
        # Step 5: Extract chunks
        # --------------------------------------------------

        chunks = [
            chunk
            for chunk, _ in reranked_results
        ]

        # --------------------------------------------------
        # Step 6: Build context
        # --------------------------------------------------

        context = ContextBuilder.build(chunks)

        # --------------------------------------------------
        # Step 7: Build prompt
        # --------------------------------------------------

        prompt = PromptBuilder.build(
            context=context,
            question=question,
        )

        # --------------------------------------------------
        # Step 8: Generate answer
        # --------------------------------------------------

        answer = await LLMService.generate(prompt)

        # --------------------------------------------------
        # Step 9: Build citations
        # --------------------------------------------------

        citations = CitationBuilder.build(chunks)

        # --------------------------------------------------
        # Step 10: Return final response
        # --------------------------------------------------

        return RAGResponse(
            answer=answer,
            citations=citations,
        )