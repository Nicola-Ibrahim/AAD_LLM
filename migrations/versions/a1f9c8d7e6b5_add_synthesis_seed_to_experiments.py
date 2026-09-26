"""add synthesis seed to experiments

Revision ID: a1f9c8d7e6b5
Revises: e4f79ded0ed4
Create Date: 2026-09-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1f9c8d7e6b5"
down_revision: Union[str, Sequence[str], None] = "e4f79ded0ed4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("experiments", schema=None) as batch_op:
        batch_op.add_column(sa.Column("synthesis_seed", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("experiments", schema=None) as batch_op:
        batch_op.drop_column("synthesis_seed")
