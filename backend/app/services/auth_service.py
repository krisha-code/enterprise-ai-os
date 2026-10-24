from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse


class AuthService:

    @staticmethod
    async def login(
        db: AsyncSession,
        email: str,
        password: str,
    ) -> TokenResponse:

        user = await UserRepository.get_by_email(
            db,
            email,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        token_data = {
            "sub": str(user.id),
            "ver": user.token_version,
        }

        access_token = create_access_token(
            token_data,
        )

        refresh_token = create_refresh_token(
            token_data,
        )

        refresh_token_hash = hash_refresh_token(
            refresh_token,
        )

        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )
        )

        await RefreshTokenRepository.create(
            db=db,
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=expires_at,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    @staticmethod
    async def refresh_token(
        db: AsyncSession,
        refresh_token: str,
    ) -> TokenResponse:

        payload = decode_refresh_token(
            refresh_token,
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        try:
            user_id = int(user_id)

        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        token_hash = hash_refresh_token(
            refresh_token,
        )

        stored_token = (
            await RefreshTokenRepository.get_by_token_hash(
                db,
                token_hash,
            )
        )

        if stored_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not recognized",
            )

        if stored_token.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if stored_token.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        if stored_token.expires_at <= datetime.now(
            timezone.utc
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            )

        user = await UserRepository.get_by_id(
            db,
            user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if payload.get("ver", 0) != user.token_version:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        await RefreshTokenRepository.revoke(
            db,
            stored_token,
        )

        token_data = {
            "sub": str(user.id),
            "ver": user.token_version,
        }

        new_access_token = create_access_token(
            token_data,
        )

        new_refresh_token = create_refresh_token(
            token_data,
        )

        new_refresh_token_hash = hash_refresh_token(
            new_refresh_token,
        )

        new_expires_at = (
            datetime.now(timezone.utc)
            + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )
        )

        await RefreshTokenRepository.create(
            db=db,
            user_id=user.id,
            token_hash=new_refresh_token_hash,
            expires_at=new_expires_at,
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    @staticmethod
    async def logout(
        db: AsyncSession,
        refresh_token: str,
    ) -> None:

        token_hash = hash_refresh_token(
            refresh_token,
        )

        stored_token = (
            await RefreshTokenRepository.get_by_token_hash(
                db,
                token_hash,
            )
        )

        if stored_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if stored_token.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has already been revoked",
            )

        await RefreshTokenRepository.revoke(
            db,
            stored_token,
        )

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:

        if not verify_password(
            current_password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )

        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password",
            )

        user.password_hash = hash_password(
            new_password,
        )
        user.must_change_password = False
        user.token_version += 1

        await db.commit()

        await RefreshTokenRepository.revoke_all_for_user(
            db,
            user.id,
        )

    @staticmethod
    async def request_password_reset(
        db: AsyncSession,
        email: str,
    ) -> str:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Password reset is unavailable until email delivery "
                "is configured."
            ),
        )

    @staticmethod
    async def reset_password(
        db: AsyncSession,
        token: str,
        new_password: str,
    ) -> None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Password reset is unavailable until email delivery "
                "is configured."
            ),
        )

    @staticmethod
    async def deactivate_user(
    db: AsyncSession,
    user_id: int,
) -> User:
        user = await UserRepository.get_by_id(
        db,
        user_id,
    )
        if not user:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
        user.is_active = False

        await db.commit()
        await db.refresh(user)
        return user


    @staticmethod
    async def activate_user(
        db: AsyncSession,
        user_id: int,
        ) -> User:
        user = await UserRepository.get_by_id(
        db,
        user_id,
    )
        if not user:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
        user.is_active = True
        await db.commit()
        await db.refresh(user)
        return user
