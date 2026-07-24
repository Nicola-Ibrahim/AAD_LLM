"""remove_run_id

Revision ID: 20260723_remove_run_id
Revises: 16af70da7e5f
Create Date: 2026-07-23 21:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260723_remove_run_id"
down_revision: Union[str, None] = "16af70da7e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("experiments", schema=None) as batch_op:
        batch_op.drop_constraint("uq_experiment_run", type_="unique")
        batch_op.drop_column("run_id")


def downgrade() -> None:
    with op.batch_alter_table("experiments", schema=None) as batch_op:
        batch_op.add_column(sa.Column("run_id", sa.Integer(), nullable=False, server_default="1"))
        batch_op.create_unique_constraint(
            "uq_experiment_run",
            ["problem_id", "dim", "mode", "llm_name", "noise_std", "run_id"],
        )
