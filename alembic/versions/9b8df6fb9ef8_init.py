from alembic import op
import sqlalchemy as sa


revision = '9b8df6fb9ef8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('utilisateurs',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('nom_complet', sa.String(length=150), nullable=True),
    sa.Column('role', sa.Enum('ADMIN', 'ORGANISATEUR', 'PARTICIPANT', name='user_role'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_utilisateurs_email'), 'utilisateurs', ['email'], unique=True)
    op.create_table('evenements',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organisateur_id', sa.Uuid(), nullable=False),
    sa.Column('titre', sa.String(length=150), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('date_debut', sa.DateTime(timezone=True), nullable=False),
    sa.Column('lieu', sa.String(length=150), nullable=True),
    sa.Column('capacite', sa.Integer(), nullable=False),
    sa.Column('statut', sa.Enum('BROUILLON', 'PUBLIE', 'TERMINE', name='event_status'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['organisateur_id'], ['utilisateurs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('billets',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('evenement_id', sa.Uuid(), nullable=False),
    sa.Column('participant_id', sa.Uuid(), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('prix', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('qr_code', sa.Text(), nullable=True),
    sa.Column('statut', sa.Enum('CREE', 'PAYE', 'UTILISE', 'ANNULE', name='ticket_status'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['evenement_id'], ['evenements.id'], ),
    sa.ForeignKeyConstraint(['participant_id'], ['utilisateurs.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('qr_code')
    )
    op.create_table('paiements',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('billet_id', sa.Uuid(), nullable=False),
    sa.Column('montant', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('moyen', sa.String(length=50), nullable=False),
    sa.Column('statut', sa.Enum('EN_ATTENTE', 'SUCCES', 'ECHEC', name='payment_status'), nullable=False),
    sa.Column('date_paiement', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['billet_id'], ['billets.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('billet_id')
    )


def downgrade() -> None:
    op.drop_table('paiements')
    op.drop_table('billets')
    op.drop_table('evenements')
    op.drop_index(op.f('ix_utilisateurs_email'), table_name='utilisateurs')
    op.drop_table('utilisateurs')
