"""Create the first organization administrator from private environment values.

Run after database migrations from the backend directory. This script never
prints or stores the administrator's password in source control.
"""
import asyncio
import getpass
import os

from sqlalchemy import select

from app.core.security import hash_password
from app.database.seed_rbac import seed_rbac
from app.database.session import AsyncSessionLocal
from app.models.organization import Organization
from app.models.role import Role
from app.models.user import User


async def main() -> None:
    email = os.getenv("BOOTSTRAP_ADMIN_EMAIL") or input("Organization admin email: ")
    email = email.strip().lower()
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD") or getpass.getpass(
        "Create a unique admin password (at least 16 characters): "
    )
    organization_name = (
        os.getenv("BOOTSTRAP_ORGANIZATION_NAME")
        or input("Organization name: ")
    ).strip()
    admin_name = os.getenv("BOOTSTRAP_ADMIN_NAME") or input("Admin name: ")
    admin_name = admin_name.strip() or "Organization Admin"

    if not email or "@" not in email:
        raise SystemExit("Set BOOTSTRAP_ADMIN_EMAIL to the admin's email address.")
    if len(password) < 16:
        raise SystemExit("Set BOOTSTRAP_ADMIN_PASSWORD to a unique password of at least 16 characters.")
    if not organization_name:
        raise SystemExit("Set BOOTSTRAP_ORGANIZATION_NAME to the organization name.")

    await seed_rbac()

    async with AsyncSessionLocal() as db:
        organization_result = await db.execute(
            select(Organization).where(Organization.name == organization_name)
        )
        organization = organization_result.scalar_one_or_none()
        if organization is None:
            organization = Organization(name=organization_name)
            db.add(organization)
            await db.flush()

        role_result = await db.execute(select(Role).where(Role.name == "admin"))
        admin_role = role_result.scalar_one()

        user_result = await db.execute(select(User).where(User.email == email))
        existing_user = user_result.scalar_one_or_none()
        if existing_user is not None:
            if (
                existing_user.role_id != admin_role.id
                or existing_user.organization_id != organization.id
            ):
                raise SystemExit(
                    "That email already belongs to a different account. "
                    "Use a new admin email; this script will not promote or move accounts."
                )
            print(f"Organization admin already exists: {email} ({organization_name}).")
            return

        db.add(
            User(
                name=admin_name or "Organization Admin",
                email=email,
                password_hash=hash_password(password),
                is_active=True,
                role_id=admin_role.id,
                organization_id=organization.id,
                must_change_password=False,
            )
        )
        await db.commit()

    print(f"Organization admin created: {email} ({organization_name}).")
    print("Keep the password private. The password itself was not printed.")


if __name__ == "__main__":
    asyncio.run(main())
