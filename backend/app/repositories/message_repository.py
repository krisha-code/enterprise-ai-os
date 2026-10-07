from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


class MessageRepository:

    @staticmethod
    async def create_message(
        db: AsyncSession,
        conversation_id: int,
        role: str,
        content: str,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        db.add(message)
        await db.commit()
        await db.refresh(message)

        return message

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        conversation_id: int,
        limit: int | None = None,
    ) -> list[Message]:

        query = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
            )
            .order_by(
                Message.created_at.desc(),
                Message.id.desc(),
            )
        )

        if limit is not None:
            query = query.limit(limit)

        result = await db.execute(query)

        messages = list(result.scalars().all())

        # We queried newest → oldest for the limit,
        # but return oldest → newest for conversation history.
        messages.reverse()

        return messages