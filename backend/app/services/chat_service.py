from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository

from app.services.conversation_history_service import (
    ConversationHistoryService,
)
from app.services.document_search_service import DocumentSearchService
from app.services.evidence_sufficiency_service import (
    EvidenceSufficiencyService,
)
from app.services.context_builder import ContextBuilder
from app.services.prompt_builder import PromptBuilder
from app.services.llm_service import LLMService
from app.services.citation_builder import CitationBuilder

from app.schemas.rag import RAGResponse


class ChatService:

    @staticmethod
    async def chat(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        question: str,
        limit: int = 5,
    ) -> RAGResponse:

        # 1. Verify that the conversation belongs to the user.
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

        # 2. Save the user's message.
        await MessageRepository.create_message(
            db=db,
            conversation_id=conversation_id,
            role="user",
            content=question,
        )

        # 3. Load recent conversation history.
        messages = await MessageRepository.get_messages(
            db=db,
            conversation_id=conversation_id,
            limit=20,
        )

        # 4. Format conversation history for the LLM.
        conversation_history = (
            ConversationHistoryService.format_messages(
                messages
            )
        )

        # 5. Retrieve and rerank relevant enterprise documents.
        #
        # Unlike search(), search_with_scores() preserves
        # the reranker scores required by the evidence gate.
        reranked_results = (
            await DocumentSearchService.search_with_scores(
                db=db,
                query=question,
                user_id=user_id,
                limit=limit,
                max_distance=None,
            )
        )

        # 6. Evaluate whether the retrieved evidence is
        # sufficiently strong to continue to answer generation.
        evidence_sufficient = (
            EvidenceSufficiencyService.evaluate(
                reranked_results
            )
        )

        # 7. If evidence is insufficient, do not call the LLM.
        if not evidence_sufficient:
            answer = (
                "I don't have enough information "
                "to answer that question."
            )

            # Store the assistant's fallback response so that
            # conversation history remains consistent.
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

        # 8. Extract the chunks from the scored results.
        #
        # ContextBuilder and CitationBuilder operate on
        # DocumentChunk objects rather than (chunk, score) pairs.
        chunks = [
            chunk
            for chunk, score in reranked_results
        ]

        # 9. Build document context.
        context = ContextBuilder.build(chunks)

        # 10. Build conversational RAG prompt.
        prompt = PromptBuilder.build(
            context=context,
            question=question,
            conversation_history=conversation_history,
        )

        # 11. Generate the answer using the local LLM.
        answer = await LLMService.generate(prompt)

        # 12. Save the assistant's answer.
        await MessageRepository.create_message(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
        )

        # 13. Build authoritative citations from the retrieved chunks.
        citations = CitationBuilder.build(chunks)

        # 14. Return answer and citations.
        return RAGResponse(
            answer=answer,
            citations=citations,
        )