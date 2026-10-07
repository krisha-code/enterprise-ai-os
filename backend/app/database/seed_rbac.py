import asyncio

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


async def seed_rbac():
    async with AsyncSessionLocal() as db:

        # -------------------------
        # 1. Create roles
        # -------------------------

        result = await db.execute(
            select(Role).where(Role.name == "user")
        )
        user_role = result.scalar_one_or_none()

        if not user_role:
            user_role = Role(name="user")
            db.add(user_role)

        result = await db.execute(
            select(Role).where(Role.name == "admin")
        )
        admin_role = result.scalar_one_or_none()

        if not admin_role:
            admin_role = Role(name="admin")
            db.add(admin_role)

        await db.flush()

        # -------------------------
        # 2. Create permissions
        # -------------------------

        permission_names = [
            "users:read",
            "users:create",
            "users:update",
            "users:delete",
        ]

        permissions = {}

        for permission_name in permission_names:
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

            permissions[permission_name] = permission

        await db.flush()

        # -------------------------
        # 3. Admin permissions
        # -------------------------

        for permission in permissions.values():

            result = await db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == admin_role.id,
                    RolePermission.permission_id == permission.id,
                )
            )

            existing = result.scalar_one_or_none()

            if not existing:
                db.add(
                    RolePermission(
                        role_id=admin_role.id,
                        permission_id=permission.id,
                    )
                )

        # -------------------------
        # 4. User permissions
        # -------------------------

        read_permission = permissions["users:read"]

        result = await db.execute(
            select(RolePermission).where(
                RolePermission.role_id == user_role.id,
                RolePermission.permission_id == read_permission.id,
            )
        )

        existing = result.scalar_one_or_none()

        if not existing:
            db.add(
                RolePermission(
                    role_id=user_role.id,
                    permission_id=read_permission.id,
                )
            )

        await db.commit()

        print("RBAC seed completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed_rbac())