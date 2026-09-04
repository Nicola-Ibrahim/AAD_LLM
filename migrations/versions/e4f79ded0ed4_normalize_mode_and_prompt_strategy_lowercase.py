"""normalize_mode_and_prompt_strategy_lowercase

Revision ID: e4f79ded0ed4
Revises: e4f79ded0ed3
Create Date: 2026-09-04 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f79ded0ed4'
down_revision: Union[str, Sequence[str], None] = 'e4f79ded0ed3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Normalize mode and prompt_strategy values to lowercase."""
    op.execute("UPDATE experiments SET mode = LOWER(mode) WHERE mode IS NOT NULL")
    op.execute(
        "UPDATE experiments SET prompt_strategy = LOWER(prompt_strategy) WHERE prompt_strategy IS NOT NULL"
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
