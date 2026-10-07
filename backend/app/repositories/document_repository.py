from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


class DocumentRepository:

    @staticmethod
    async def get_by_user(
        db: AsyncSession,
        user_id: int,
    ) -> list[Document]:

        result = await db.execute(
            select(Document)
            .where(
                Document.user_id == user_id
            )
            .order_by(
                Document.id.desc()
            )
        )

        return list(
            result.scalars().all()
        )