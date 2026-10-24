"""add mandatory temporary-password change flag

Revision ID: e23a1024c715
Revises: 5c91a2e8d7f4
Create Date: 2026-10-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e23a1024c715"
down_revision: Union[str, Sequence[str], None] = "5c91a2e8d7f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "token_version",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "token_version")
    op.drop_column("users", "must_change_password")
