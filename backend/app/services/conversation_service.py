from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.conversation_repository import ConversationRepository


class ConversationService:

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        user_id: int,
        title: str,
    ):
        title = title.strip()

        if not title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation title cannot be empty",
            )

        return await ConversationRepository.create_conversation(
            db=db,
            user_id=user_id,
            title=title,
        )

    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
    ):
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

        return conversation

    @staticmethod
    async def get_user_conversations(
        db: AsyncSession,
        user_id: int,
    ):
        return await ConversationRepository.get_user_conversations(
            db=db,
            user_id=user_id,
        )