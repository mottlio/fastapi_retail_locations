"""add service boolean columns to gas_stations

Revision ID: 1c551a8ef835
Revises: a18c6ba9f537
Create Date: 2025-10-21 10:16:36.849042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c551a8ef835'
down_revision: Union[str, Sequence[str], None] = 'a18c6ba9f537'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add service boolean columns to gas_stations table
    op.add_column('gas_stations', sa.Column('service_carwash', sa.Boolean(), nullable=True))
    op.add_column('gas_stations', sa.Column('service_food', sa.Boolean(), nullable=True))
    op.add_column('gas_stations', sa.Column('service_coffee', sa.Boolean(), nullable=True))
    op.add_column('gas_stations', sa.Column('service_shop', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove service boolean columns from gas_stations table
    op.drop_column('gas_stations', 'service_shop')
    op.drop_column('gas_stations', 'service_coffee')
    op.drop_column('gas_stations', 'service_food')
    op.drop_column('gas_stations', 'service_carwash')
