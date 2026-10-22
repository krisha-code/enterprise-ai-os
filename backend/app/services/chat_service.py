import logging

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.conversation_repository import (
    ConversationRepository,
)
from app.repositories.message_repository import (
    MessageRepository,
)
from app.services.conversation_history_service import (
    ConversationHistoryService,
)
from app.services.query_rewrite_service import QueryRewriteService
from app.services.document_search_service import DocumentSearchService
from app.services.evidence_sufficiency_service import (
    EvidenceSufficiencyService,
)
from app.services.context_builder import ContextBuilder
from app.services.prompt_builder import PromptBuilder
from app.services.llm_service import LLMService
from app.services.citation_builder import CitationBuilder
from app.services.answer_validation_service import (
    AnswerValidationService,
)
from app.schemas.rag import RAGResponse

logger = logging.getLogger("enterprise-ai-os")


class ChatService:

    @staticmethod
    async def chat(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        question: str,
        limit: int = 5,
    ) -> RAGResponse:

        # 1. Verify conversation ownership.
        conversation = await ConversationRepository.get_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # 2. Load conversation history before saving the current question.
        messages = await MessageRepository.get_messages(
            db=db,
            conversation_id=conversation_id,
            limit=20,
        )

        conversation_history = ConversationHistoryService.format_messages(
            messages
        )

        # 3. Save the user's question.
        await MessageRepository.create_message(
            db=db,
            conversation_id=conversation_id,
            role="user",
            content=question,
        )

        # 4. Rewrite the question for retrieval.
        retrieval_query = QueryRewriteService.rewrite(
            question=question,
            conversation_history=conversation_history,
        )

        # 5. Retrieve and rerank evidence.
        reranked_results = (
            await DocumentSearchService.search_with_scores(
                db=db,
                query=retrieval_query,
                user_id=user_id,
                limit=limit,
                max_distance=None,
            )
        )

        # 6. Check evidence sufficiency before generating an answer.
        evidence_sufficient = EvidenceSufficiencyService.evaluate(
            reranked_results
        )

        if not evidence_sufficient:
            answer = (
                "I don't have enough information "
                "to answer that question."
            )

            await MessageRepository.create_message(
                db=db,
                conversation_id=conversation_id,
                role="assistant",
                content=answer,
            )

            return RAGResponse(
                answer=answer,
                citations=[],
            )

        # 7. Build context from the retrieved chunks.
        chunks = [chunk for chunk, score in reranked_results]
        context = ContextBuilder.build(chunks)

        # 8. Build the prompt.
        prompt = PromptBuilder.build(
            context=context,
            question=question,
            conversation_history=conversation_history,
        )

        # 9. Generate an answer and handle common LLM failures.
        try:
            answer = await LLMService.generate(prompt)
        except (httpx.HTTPError, KeyError, ValueError):
            logger.exception(
                "LLM generation failed for conversation_id=%s",
                conversation_id,
            )

            # Persist an explicit failure outcome so the saved user
            # message is not left without any corresponding assistant turn.
            try:
                await MessageRepository.create_message(
                    db=db,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=(
                        "I couldn't generate an answer because the answer "
                        "service is temporarily unavailable. Please try again."
                    ),
                )
            except Exception:
                logger.exception(
                    "Could not save LLM failure outcome for conversation_id=%s",
                    conversation_id,
                )

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "The answer service is temporarily unavailable. "
                    "Please try again."
                ),
            ) from None

        # 10. Validate the generated answer against retrieved evidence.
        is_valid = AnswerValidationService.validate(
            answer=answer,
            context=context,
            question=question,
        )

        used_fallback = False
        fallback_source_id = None

        # 11. If validation fails, extract a labeled section from
        # a single source when an appropriate section is available.
        if not is_valid:
            question_lower = question.lower()
            fallback_label = None

            if "disadvantage" in question_lower:
                fallback_label = "Disadvantages"
            elif (
                "advantage" in question_lower
                or any(
                    phrase in question_lower
                    for phrase in (
                        "why is it suitable",
                        "why is it good",
                        "large-area surveying",
                        "large area surveying",
                    )
                )
            ):
                fallback_label = "Advantages"

            extracted = None

            if fallback_label:
                extracted = (
                    AnswerValidationService
                    .extract_labeled_section_with_source(
                        context=context,
                        label=fallback_label,
                    )
                )

            if extracted:
                answer, fallback_source_id = extracted
                used_fallback = True
            else:
                answer = (
                    "I don't have enough information "
                    "to answer that question."
                )

        # 12. Save the final answer.
        await MessageRepository.create_message(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
        )

        # 13. Select citations appropriate to the returned answer.
        if used_fallback and fallback_source_id is not None:
            all_citations = CitationBuilder.build(chunks)
            citations = [
                citation
                for citation in all_citations
                if citation.source_id == fallback_source_id
            ]
        elif is_valid:
            citations = CitationBuilder.build_relevant(
                chunks=chunks,
                answer=answer,
                question=question,
            )
        else:
            citations = []

        # 14. Return the answer and its citations.
        return RAGResponse(
            answer=answer,
            citations=citations,
        )
