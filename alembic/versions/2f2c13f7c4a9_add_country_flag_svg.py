from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "2f2c13f7c4a9"
down_revision = "b7c6d8e9a0f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("countries", sa.Column("flag_svg", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("countries", "flag_svg")

