from alembic import op
import sqlalchemy as sa


revision = '7d3aa06b4b02'
down_revision = '4c1b2a7d8e01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        with op.batch_alter_table("billets", recreate="always") as batch_op:
            batch_op.alter_column("participant_id", existing_type=sa.Uuid(), nullable=True)
            batch_op.add_column(sa.Column("guest_email", sa.String(length=320), nullable=True))
            batch_op.add_column(sa.Column("guest_nom_complet", sa.String(length=200), nullable=True))
            batch_op.add_column(sa.Column("guest_phone", sa.String(length=50), nullable=True))
    else:
        op.alter_column("billets", "participant_id", existing_type=sa.Uuid(), nullable=True)
        op.add_column("billets", sa.Column("guest_email", sa.String(length=320), nullable=True))
        op.add_column("billets", sa.Column("guest_nom_complet", sa.String(length=200), nullable=True))
        op.add_column("billets", sa.Column("guest_phone", sa.String(length=50), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        with op.batch_alter_table("billets", recreate="always") as batch_op:
            batch_op.drop_column("guest_phone")
            batch_op.drop_column("guest_nom_complet")
            batch_op.drop_column("guest_email")
            batch_op.alter_column("participant_id", existing_type=sa.Uuid(), nullable=False)
    else:
        op.drop_column("billets", "guest_phone")
        op.drop_column("billets", "guest_nom_complet")
        op.drop_column("billets", "guest_email")
        op.alter_column("billets", "participant_id", existing_type=sa.Uuid(), nullable=False)

