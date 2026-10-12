from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.repositories.conversation_repository import (
    ConversationRepository,
)
from app.repositories.message_repository import (
    MessageRepository,
)

from app.services.conversation_history_service import (
    ConversationHistoryService,
)
from app.services.query_rewrite_service import (
    QueryRewriteService,
)
from app.services.document_search_service import (
    DocumentSearchService,
)
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

        # 2. Load previous conversation history BEFORE saving
        # the current question.
        messages = await MessageRepository.get_messages(
            db=db,
            conversation_id=conversation_id,
            limit=20,
        )

        # 3. Format the previous conversation history.
        conversation_history = (
            ConversationHistoryService.format_messages(
                messages
            )
        )

        # 4. Save the original user question.
        await MessageRepository.create_message(
            db=db,
            conversation_id=conversation_id,
            role="user",
            content=question,
        )

        # 5. Rewrite the question for document retrieval.
        retrieval_query = QueryRewriteService.rewrite(
            question=question,
            conversation_history=conversation_history,
        )

        # 6. Retrieve and rerank using the rewritten query.
        # Preserve reranker scores for the evidence gate.
        reranked_results = (
            await DocumentSearchService.search_with_scores(
                db=db,
                query=retrieval_query,
                user_id=user_id,
                limit=limit,
                max_distance=None,
            )
        )


        # 7. Evaluate whether the retrieved evidence is sufficient.
        evidence_sufficient = (
            EvidenceSufficiencyService.evaluate(
                reranked_results
            )
        )

        # 8. Refuse unsupported questions without calling the LLM.
        if not evidence_sufficient:
            answer = (
                "I don't have enough information "
                "to answer that question."
            )

            # Persist the refusal in conversation history.
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

        # 9. Extract chunks from the scored retrieval results.
        chunks = [
            chunk
            for chunk, score in reranked_results
        ]

        # 10. Build context from the retrieved document chunks.
        context = ContextBuilder.build(chunks)

        # 11. Build the answer prompt.
        # Use the ORIGINAL question and previous conversation.
        prompt = PromptBuilder.build(
            context=context,
            question=question,
            conversation_history=conversation_history,
        )

        # 12. Generate the answer using the local LLM.
        answer = await LLMService.generate(prompt)

        # 13. Persist the assistant's answer.
        await MessageRepository.create_message(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
        )

        # 14. Build citations from the retrieved chunks.
        citations = CitationBuilder.build(chunks)

        # 15. Return the answer and citations.
        return RAGResponse(
            answer=answer,
            citations=citations,
        )
