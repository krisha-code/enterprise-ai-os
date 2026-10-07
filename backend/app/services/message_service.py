from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository


class MessageService:

    @staticmethod
    async def create_message(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        role: str,
        content: str,
    ):
        content = content.strip()

        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content cannot be empty",
            )

        if role not in {"user", "assistant"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid message role",
            )

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

        return await MessageRepository.create_message(
            db=db,
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

    @staticmethod
    async def get_messages(
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

        return await MessageRepository.get_messages(
            db=db,
            conversation_id=conversation_id,
        )