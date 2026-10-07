"""add document active status

Revision ID: 9f45f9a418f8
Revises: 8b895e09ffc7
Create Date: 2026-10-05 19:54:43.430002

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f45f9a418f8"
down_revision: Union[str, Sequence[str], None] = "8b895e09ffc7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "documents",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "documents",
        "is_active",
    )