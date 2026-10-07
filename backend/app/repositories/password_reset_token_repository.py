from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:

        token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            used=False,
            created_at=datetime.now(timezone.utc),
        )

        db.add(token)
        await db.commit()
        await db.refresh(token)

        return token

    @staticmethod
    async def get_by_token_hash(
        db: AsyncSession,
        token_hash: str,
    ) -> PasswordResetToken | None:

        result = await db.execute(
            select(PasswordResetToken)
            .where(
                PasswordResetToken.token_hash == token_hash
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def mark_used(
        db: AsyncSession,
        token: PasswordResetToken,
    ) -> None:

        token.used = True

        await db.commit()