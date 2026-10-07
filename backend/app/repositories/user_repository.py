from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        user_data: UserCreate,
        password_hash: str,
        role_id: int,
    ) -> User:
        user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=password_hash,
            role_id=role_id,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def get_by_email(
        db: AsyncSession,
        email: str,
    ) -> User | None:
        result = await db.execute(
            select(User)
            .where(User.email == email)
            .options(
                selectinload(User.role)
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
    ) -> list[User]:
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.role)
            )
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())

    @staticmethod
    async def get_filtered(
        db: AsyncSession,
        name: str | None = None,
        skip: int = 0,
        limit: int = 10,
        sort_by: str = "id",
        order: str = "asc",
    ) -> list[User]:

        query = select(User).options(
            selectinload(User.role)
        )

        if name:
            query = query.where(
                User.name == name
            )

        sortable_columns = {
            "id": User.id,
            "name": User.name,
            "email": User.email,
        }

        column = sortable_columns.get(
            sort_by,
            User.id,
        )

        if order.lower() == "desc":
            query = query.order_by(
                column.desc()
            )
        else:
            query = query.order_by(
                column.asc()
            )

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)

        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        user_id: int,
    ) -> User | None:

        result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.role)
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession,
        user: User,
        user_data: UserUpdate,
    ) -> User:

        if user_data.name is not None:
            user.name = user_data.name

        if user_data.email is not None:
            user.email = user_data.email

        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def delete(
        db: AsyncSession,
        user: User,
    ) -> None:

        await db.delete(user)
        await db.commit()