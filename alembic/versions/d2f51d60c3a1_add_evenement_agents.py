from alembic import op
import sqlalchemy as sa


revision = "d2f51d60c3a1"
down_revision = "cc01e537aa6b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_enum
                    WHERE enumlabel = 'AGENT'
                      AND enumtypid = 'user_role'::regtype
                ) THEN
                    ALTER TYPE user_role ADD VALUE 'AGENT';
                END IF;
            END $$;
            """
        )

    op.create_table(
        "evenement_agents",
        sa.Column(
            "evenement_id",
            sa.Uuid(),
            sa.ForeignKey("evenements.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "agent_id",
            sa.Uuid(),
            sa.ForeignKey("utilisateurs.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )
    op.create_index("ix_evenement_agents_evenement_id", "evenement_agents", ["evenement_id"])
    op.create_index("ix_evenement_agents_agent_id", "evenement_agents", ["agent_id"])


def downgrade() -> None:
    op.drop_index("ix_evenement_agents_agent_id", table_name="evenement_agents")
    op.drop_index("ix_evenement_agents_evenement_id", table_name="evenement_agents")
    op.drop_table("evenement_agents")
