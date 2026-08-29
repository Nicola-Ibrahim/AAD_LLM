"""update_noise_model_default_to_heteroscedastic

Revision ID: e4f79ded0ed3
Revises: 0d231c4dae51
Create Date: 2026-08-29 13:44:30.485922

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f79ded0ed3'
down_revision: Union[str, Sequence[str], None] = '0d231c4dae51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema and existing records."""
    op.execute(
        "UPDATE experiments SET noise_model = 'heteroscedastic' WHERE noise_model = 'multiplicative'"
    )
    with op.batch_alter_table("experiments", schema=None) as batch_op:
        batch_op.alter_column(
            "noise_model",
            existing_type=sa.String(),
            server_default=sa.text("'heteroscedastic'"),
            nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema and records."""
    with op.batch_alter_table("experiments", schema=None) as batch_op:
        batch_op.alter_column(
            "noise_model",
            existing_type=sa.String(),
            server_default=sa.text("'multiplicative'"),
            nullable=False,
        )
    op.execute(
        "UPDATE experiments SET noise_model = 'multiplicative' WHERE noise_model = 'heteroscedastic'"
    )

