from alembic import op
import sqlalchemy as sa


revision = '35061bc46e4f'
down_revision = '9aebbdde36e5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('billets', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))
    op.add_column('evenements', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))
    op.add_column('paiements', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))
    op.add_column('paiements', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))
    op.add_column('refresh_tokens', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))
    op.add_column('utilisateurs', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))


def downgrade() -> None:
    op.drop_column('utilisateurs', 'updated_at')
    op.drop_column('refresh_tokens', 'updated_at')
    op.drop_column('paiements', 'updated_at')
    op.drop_column('paiements', 'created_at')
    op.drop_column('evenements', 'updated_at')
    op.drop_column('billets', 'updated_at')
