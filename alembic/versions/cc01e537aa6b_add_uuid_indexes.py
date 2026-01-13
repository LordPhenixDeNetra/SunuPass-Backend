from alembic import op
import sqlalchemy as sa


revision = 'cc01e537aa6b'
down_revision = '7d3aa06b4b02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_evenements_organisateur_id", "evenements", ["organisateur_id"], unique=False)

    op.create_index("ix_billets_evenement_id", "billets", ["evenement_id"], unique=False)
    op.create_index("ix_billets_participant_id", "billets", ["participant_id"], unique=False)
    op.create_index("ix_billets_ticket_type_id", "billets", ["ticket_type_id"], unique=False)
    op.create_index("ix_billets_promo_code_id", "billets", ["promo_code_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_billets_promo_code_id", table_name="billets")
    op.drop_index("ix_billets_ticket_type_id", table_name="billets")
    op.drop_index("ix_billets_participant_id", table_name="billets")
    op.drop_index("ix_billets_evenement_id", table_name="billets")

    op.drop_index("ix_evenements_organisateur_id", table_name="evenements")
