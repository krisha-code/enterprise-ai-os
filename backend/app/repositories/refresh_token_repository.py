from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:

        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked=False,
            created_at=datetime.now(),
        )

        db.add(refresh_token)

        await db.commit()

        await db.refresh(refresh_token)

        return refresh_token

    @staticmethod
    async def get_by_token_hash(
        db: AsyncSession,
        token_hash: str,
    ) -> RefreshToken | None:

        result = await db.execute(
            select(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def revoke(
        db: AsyncSession,
        refresh_token: RefreshToken,
    ) -> None:

        refresh_token.revoked = True

        await db.commit()


    @staticmethod
    async def revoke_all_for_user(
        db: AsyncSession,
        user_id: int,
    ) -> None:

        result = await db.execute(
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,
            )
        )

        tokens = result.scalars().all()

        for token in tokens:
            token.revoked = True

        await db.commit()