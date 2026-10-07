import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.database.session import AsyncSessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User


PERMISSIONS = [
    "users:read",
    "users:create",
    "users:update",
    "users:delete",
]


async def main():
    async with AsyncSessionLocal() as db:

        # ----------------------------------------
        # 1. Create permissions
        # ----------------------------------------

        permissions = {}

        for permission_name in PERMISSIONS:
            result = await db.execute(
                select(Permission).where(
                    Permission.name == permission_name
                )
            )

            permission = result.scalar_one_or_none()

            if not permission:
                permission = Permission(
                    name=permission_name
                )
                db.add(permission)
                await db.flush()

            permissions[permission_name] = permission

        # ----------------------------------------
        # 2. Create roles
        # ----------------------------------------

        result = await db.execute(
            select(Role).where(Role.name == "admin")
        )

        admin_role = result.scalar_one_or_none()

        if not admin_role:
            admin_role = Role(name="admin")
            db.add(admin_role)
            await db.flush()

        result = await db.execute(
            select(Role).where(Role.name == "user")
        )

        user_role = result.scalar_one_or_none()

        if not user_role:
            user_role = Role(name="user")
            db.add(user_role)
            await db.flush()

        # ----------------------------------------
        # 3. Give admin all permissions
        # ----------------------------------------

        for permission in permissions.values():

            result = await db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == admin_role.id,
                    RolePermission.permission_id == permission.id,
                )
            )

            role_permission = result.scalar_one_or_none()

            if not role_permission:
                db.add(
                    RolePermission(
                        role_id=admin_role.id,
                        permission_id=permission.id,
                    )
                )

        # ----------------------------------------
        # 4. Give normal users read permission
        # ----------------------------------------

        result = await db.execute(
            select(RolePermission).where(
                RolePermission.role_id == user_role.id,
                RolePermission.permission_id
                == permissions["users:read"].id,
            )
        )

        user_read_permission = result.scalar_one_or_none()

        if not user_read_permission:
            db.add(
                RolePermission(
                    role_id=user_role.id,
                    permission_id=permissions["users:read"].id,
                )
            )

        # ----------------------------------------
        # 5. Create first admin user
        # ----------------------------------------

        admin_email = "admin@example.com"

        result = await db.execute(
            select(User).where(
                User.email == admin_email
            )
        )

        admin_user = result.scalar_one_or_none()

        if not admin_user:
            admin_user = User(
                name="Admin",
                email=admin_email,
                password_hash=hash_password("Admin123"),
                is_active=True,
                role_id=admin_role.id,
            )

            db.add(admin_user)

        await db.commit()

        print()
        print("RBAC seed completed successfully.")
        print()
        print("Admin login:")
        print("Email: admin@example.com")
        print("Password: Admin123")
        print()
        print("Permissions:")
        for permission_name in PERMISSIONS:
            print(f"- {permission_name}")


if __name__ == "__main__":
    asyncio.run(main())