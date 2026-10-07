import asyncio

from sqlalchemy import text

from app.database.session import AsyncSessionLocal


async def test_connection():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT version()")
        )

        print(result.scalar())


asyncio.run(test_connection())