"""add opening_hours_display to gas_stations

Revision ID: b822ba0ea0e5
Revises: 1c551a8ef835
Create Date: 2025-10-24 14:44:33.483740

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b822ba0ea0e5'
down_revision: Union[str, Sequence[str], None] = '1c551a8ef835'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add opening_hours_display column to gas_stations table
    op.add_column('gas_stations', sa.Column('opening_hours_display', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove opening_hours_display column from gas_stations table
    op.drop_column('gas_stations', 'opening_hours_display')
