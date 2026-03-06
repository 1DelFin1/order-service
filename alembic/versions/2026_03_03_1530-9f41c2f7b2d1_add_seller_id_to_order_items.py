"""add seller_id to order_items

Revision ID: 9f41c2f7b2d1
Revises: 348e30ee2a6c
Create Date: 2026-03-03 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f41c2f7b2d1"
down_revision: Union[str, Sequence[str], None] = "348e30ee2a6c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("order_items", sa.Column("seller_id", sa.Uuid(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("order_items", "seller_id")
