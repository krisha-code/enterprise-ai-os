"""add document processing status

Revision ID: 3f2cb6de3baf
Revises: 9f45f9a418f8
Create Date: 2026-10-20 17:52:34.466035

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f2cb6de3baf'
down_revision: Union[str, Sequence[str], None] = '9f45f9a418f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "processing_status",
            sa.String(length=20),
            nullable=False,
            server_default="completed",
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "processing_error",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("documents", "processing_error")
    op.drop_column("documents", "processing_status")
