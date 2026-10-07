import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.database.session import AsyncSessionLocal
from app.models.role import Role
from app.models.user import User


async def create_test_user():

    email = "document.tester@example.com"
    password = "DocumentTest123"
    name = "Document Tester"

    async with AsyncSessionLocal() as db:

        # Check if user already exists
        result = await db.execute(
            select(User).where(
                User.email == email
            )
        )

        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("User already exists.")
            print(f"Email: {email}")
            print(f"Password: {password}")
            print(f"User ID: {existing_user.id}")
            return

        # Find default user role
        result = await db.execute(
            select(Role).where(
                Role.name == "user"
            )
        )

        role = result.scalar_one_or_none()

        if role is None:
            print("Default 'user' role does not exist.")
            return

        # Create user
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role_id=role.id,
            is_active=True,
        )

        db.add(user)

        await db.commit()
        await db.refresh(user)

        print("Test user created successfully.")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"User ID: {user.id}")


asyncio.run(create_test_user())