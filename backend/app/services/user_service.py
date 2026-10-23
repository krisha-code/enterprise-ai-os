from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)

class UserService:

    @staticmethod
    async def create_user(
        db: AsyncSession,
        user_data: UserCreate,
        organization_id: int,
    ) -> User:

        existing_user = await UserRepository.get_by_email(
            db,
            user_data.email,
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

        result = await db.execute(
            select(Role).where(
                Role.name == "user"
            )
        )

        user_role = result.scalar_one_or_none()

        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Default user role is not configured",
            )

        password_hash = hash_password(
            user_data.password,
        )

        return await UserRepository.create(
            db,
            user_data,
            password_hash,
            user_role.id,
            organization_id,
        )

    @staticmethod
    async def get_users(
        db: AsyncSession,
        organization_id: int,
        name: str | None = None,
        skip: int = 0,
        limit: int = 10,
        sort_by: str = "id",
        order: str = "asc",
    ) -> list[User]:

        return await UserRepository.get_filtered(
            db,
            organization_id,
            name,
            skip,
            limit,
            sort_by,
            order,
        )

    @staticmethod
    async def get_user(
        db: AsyncSession,
        user_id: int,
        organization_id: int,
    ) -> User:

        user = await UserRepository.get_by_id(
            db,
            user_id,
            organization_id,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: int,
        user_data: UserUpdate,
        organization_id: int,
    ) -> User:

        user = await UserRepository.get_by_id(
            db,
            user_id,
            organization_id,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user_data.email is not None:

            existing_user = await UserRepository.get_by_email(
                db,
                user_data.email,
            )

            if (
                existing_user
                and existing_user.id != user.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists",
                )

        return await UserRepository.update(
            db,
            user,
            user_data,
        )

    @staticmethod
    async def delete_user(
        db: AsyncSession,
        user_id: int,
        organization_id: int,
    ) -> None:

        user = await UserRepository.get_by_id(
            db,
            user_id,
            organization_id,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        await UserRepository.delete(
            db,
            user,
        )
    @staticmethod
    async def deactivate_user(
        db: AsyncSession,
        user_id: int,
        organization_id: int,
    ) -> User:

        user = await UserRepository.get_by_id(
            db,
            user_id,
            organization_id,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.is_active = False

        await db.commit()
        await db.refresh(user)

        # Revoke all existing refresh tokens.
        await RefreshTokenRepository.revoke_all_for_user(
            db,
            user.id,
        )

        return user

    @staticmethod
    async def activate_user(
        db: AsyncSession,
        user_id: int,
        organization_id: int,
    ) -> User:

        user = await UserRepository.get_by_id(
            db,
            user_id,
            organization_id,
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
