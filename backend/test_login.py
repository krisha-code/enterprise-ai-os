import asyncio

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.user import User


async def main():
    async with AsyncSessionLocal() as db:

        result = await db.execute(
            select(User.id, User.name, User.email)
        )

        users = result.all()

        print("\nUsers currently in database:")
        print("-" * 50)

        for user_id, name, email in users:
            print("ID:", user_id)
            print("NAME:", name)
            print("EMAIL:", repr(email))
            print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())