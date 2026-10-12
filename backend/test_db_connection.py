import asyncio

from sqlalchemy import text

from app.database.session import AsyncSessionLocal


async def check_database_connection():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT version()"))
        return result.scalar()


def test_connection():
    version = asyncio.run(check_database_connection())
    assert version is not None
    print(version)
