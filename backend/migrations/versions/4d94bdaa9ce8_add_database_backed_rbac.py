"""add database backed RBAC

Revision ID: 4d94bdaa9ce8
Revises: a8d27fa66f4c
Create Date: 2026-08-10 01:19:47.987997

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d94bdaa9ce8'
down_revision: Union[str, Sequence[str], None] = 'a8d27fa66f4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create roles table
    op.create_table(
        "roles",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "name",
            sa.String(length=50),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_roles_id",
        "roles",
        ["id"],
        unique=False,
    )

    # 2. Create permissions table
    op.create_table(
        "permissions",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_permissions_id",
        "permissions",
        ["id"],
        unique=False,
    )

    # 3. Create role_permissions table
    op.create_table(
        "role_permissions",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            sa.Integer(),
            sa.ForeignKey(
                "roles.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "permission_id",
            sa.Integer(),
            sa.ForeignKey(
                "permissions.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
    )

    # 4. Create the default roles
    op.execute(
        """
        INSERT INTO roles (name)
        VALUES ('user'), ('admin')
        """
    )

    # 5. Add role_id temporarily nullable
    op.add_column(
        "users",
        sa.Column(
            "role_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    # 6. Connect existing users to their roles
    op.execute(
        """
        UPDATE users
        SET role_id = roles.id
        FROM roles
        WHERE users.role = roles.name
        """
    )

    # 7. Make role_id required
    op.alter_column(
        "users",
        "role_id",
        nullable=False,
    )

    # 8. Add foreign key
    op.create_foreign_key(
        "fk_users_role_id_roles",
        "users",
        "roles",
        ["role_id"],
        ["id"],
    )

    # 9. Remove the old string role
    op.drop_column(
        "users",
        "role",
    )


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE users
        SET role = roles.name
        FROM roles
        WHERE users.role_id = roles.id
        """
    )

    op.alter_column(
        "users",
        "role",
        nullable=False,
    )

    op.drop_constraint(
        "fk_users_role_id_roles",
        "users",
        type_="foreignkey",
    )

    op.drop_column(
        "users",
        "role_id",
    )

    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
