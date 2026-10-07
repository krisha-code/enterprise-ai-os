"""recreate users table with password hash

Revision ID: bd4bcf927b7f
Revises: 9a6a35904d76
Create Date: 2026-08-06 19:30:53.940586

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bd4bcf927b7f"
down_revision: Union[str, Sequence[str], None] = "9a6a35904d76"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "users",
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "users",
        "password_hash",
    )