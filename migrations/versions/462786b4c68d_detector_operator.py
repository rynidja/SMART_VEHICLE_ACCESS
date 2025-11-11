"""detector->operator

Revision ID: 462786b4c68d
Revises: ebc7e7956c0b
Create Date: 2025-11-09 22:14:01.707999

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '462786b4c68d'
down_revision: Union[str, Sequence[str], None] = 'ebc7e7956c0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
