"""add organizations and assign existing users and documents

Revision ID: 5c91a2e8d7f4
Revises: 3f2cb6de3baf
Create Date: 2026-10-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5c91a2e8d7f4"
down_revision: Union[str, Sequence[str], None] = "3f2cb6de3baf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        "ix_organizations_id",
        "organizations",
        ["id"],
        unique=False,
    )

    op.add_column(
        "users",
        sa.Column("organization_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("organization_id", sa.Integer(), nullable=True),
    )

    op.execute(
        "INSERT INTO organizations (name) VALUES ('Default Organization')"
    )
    op.execute(
        """
        UPDATE users
        SET organization_id = organizations.id
        FROM organizations
        WHERE organizations.name = 'Default Organization'
        """
    )
    op.execute(
        """
        UPDATE documents
        SET organization_id = users.organization_id
        FROM users
        WHERE documents.user_id = users.id
        """
    )

    op.alter_column("users", "organization_id", nullable=False)
    op.alter_column("documents", "organization_id", nullable=False)

    op.create_foreign_key(
        "fk_users_organization_id_organizations",
        "users",
        "organizations",
        ["organization_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_documents_organization_id_organizations",
        "documents",
        "organizations",
        ["organization_id"],
        ["id"],
    )
    op.create_index(
        "ix_users_organization_id",
        "users",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_documents_organization_id",
        "documents",
        ["organization_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_documents_organization_id", table_name="documents")
    op.drop_index("ix_users_organization_id", table_name="users")
    op.drop_constraint(
        "fk_documents_organization_id_organizations",
        "documents",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_users_organization_id_organizations",
        "users",
        type_="foreignkey",
    )
    op.drop_column("documents", "organization_id")
    op.drop_column("users", "organization_id")
    op.drop_index("ix_organizations_id", table_name="organizations")
    op.drop_table("organizations")
