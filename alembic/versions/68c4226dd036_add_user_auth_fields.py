from alembic import op
import sqlalchemy as sa


revision = '68c4226dd036'
down_revision = '9b8df6fb9ef8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('utilisateurs', sa.Column('hashed_password', sa.String(length=255), nullable=True))
    op.add_column(
        'utilisateurs',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_column('utilisateurs', 'is_active')
    op.drop_column('utilisateurs', 'hashed_password')
