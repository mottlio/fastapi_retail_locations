"""Add services column to gas_stations

Revision ID: a18c6ba9f537
Revises: c4febcd83c28
Create Date: 2025-10-13 13:31:01.957721

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a18c6ba9f537'
down_revision: Union[str, Sequence[str], None] = 'c4febcd83c28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
