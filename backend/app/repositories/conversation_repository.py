from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation


class ConversationRepository:

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        user_id: int,
        title: str,
    ) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            title=title,
        )

        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        return conversation

    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
    ) -> Conversation | None:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_conversations(
        db: AsyncSession,
        user_id: int,
    ) -> list[Conversation]:
        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
            )
            .order_by(Conversation.created_at.desc())
        )

        return list(result.scalars().all())