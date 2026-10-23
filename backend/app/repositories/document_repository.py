from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


class DocumentRepository:

    @staticmethod
    async def get_by_user(
        db: AsyncSession,
        organization_id: int,
    ) -> list[Document]:
        result = await db.execute(
            select(Document)
            .where(
                Document.organization_id == organization_id,
                Document.is_active.is_(True),
            )
            .order_by(Document.id.desc())
        )

        return list(result.scalars().all())

    @staticmethod
    async def get_by_id_and_user(
        db: AsyncSession,
        document_id: int,
        user_id: int,
    ) -> Document | None:
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id,
                Document.is_active.is_(True),
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id_and_organization(
        db: AsyncSession,
        document_id: int,
        organization_id: int,
    ) -> Document | None:
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.organization_id == organization_id,
                Document.is_active.is_(True),
            )
        )

        return result.scalar_one_or_none()
