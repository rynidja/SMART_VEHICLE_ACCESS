"""fix timestamps

Revision ID: 46fde30a9aa3
Revises: 462786b4c68d
Create Date: 2025-11-11 16:02:35.401133

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46fde30a9aa3'
down_revision: Union[str, Sequence[str], None] = '462786b4c68d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
