from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "f0a5a6fbe2c3"
down_revision = "d2f51d60c3a1"
branch_labels = None
depends_on = None


def _insert_missing_subtype_rows(
    *,
    dialect: str,
    subtype_table: str,
    role_value: str,
) -> None:
    if dialect == "postgresql":
        op.execute(
            sa.text(
                f"""
                INSERT INTO {subtype_table} (id)
                SELECT u.id
                FROM utilisateurs u
                WHERE u.role = :role
                ON CONFLICT (id) DO NOTHING
                """
            ).bindparams(role=role_value)
        )
        return

    op.execute(
        sa.text(
            f"""
            INSERT OR IGNORE INTO {subtype_table} (id)
            SELECT u.id
            FROM utilisateurs u
            WHERE u.role = :role
            """
        ).bindparams(role=role_value)
    )


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    op.create_table(
        "admins",
        sa.Column("id", sa.Uuid(), sa.ForeignKey("utilisateurs.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "organisateurs",
        sa.Column("id", sa.Uuid(), sa.ForeignKey("utilisateurs.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "participants",
        sa.Column("id", sa.Uuid(), sa.ForeignKey("utilisateurs.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "agents",
        sa.Column("id", sa.Uuid(), sa.ForeignKey("utilisateurs.id", ondelete="CASCADE"), primary_key=True),
    )

    _insert_missing_subtype_rows(dialect=dialect, subtype_table="admins", role_value="ADMIN")
    _insert_missing_subtype_rows(dialect=dialect, subtype_table="organisateurs", role_value="ORGANISATEUR")
    _insert_missing_subtype_rows(dialect=dialect, subtype_table="participants", role_value="PARTICIPANT")
    _insert_missing_subtype_rows(dialect=dialect, subtype_table="agents", role_value="AGENT")

    op.create_table(
        "evenement_agents_new",
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
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO evenement_agents_new (evenement_id, agent_id)
            SELECT ea.evenement_id, ea.agent_id
            FROM evenement_agents ea
            JOIN agents a ON a.id = ea.agent_id
            """
        )
    )
    op.drop_index("ix_evenement_agents_agent_id", table_name="evenement_agents")
    op.drop_index("ix_evenement_agents_evenement_id", table_name="evenement_agents")
    op.drop_table("evenement_agents")
    op.rename_table("evenement_agents_new", "evenement_agents")
    op.create_index("ix_evenement_agents_evenement_id", "evenement_agents", ["evenement_id"])
    op.create_index("ix_evenement_agents_agent_id", "evenement_agents", ["agent_id"])

    op.create_table(
        "ticket_scans_new",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "billet_id",
            sa.Uuid(),
            sa.ForeignKey("billets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "agent_id",
            sa.Uuid(),
            sa.ForeignKey("agents.id"),
            nullable=False,
        ),
        sa.Column("result", sa.String(length=30), nullable=False),
        sa.Column(
            "scanned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO ticket_scans_new (id, billet_id, agent_id, result, scanned_at)
            SELECT ts.id, ts.billet_id, ts.agent_id, ts.result, ts.scanned_at
            FROM ticket_scans ts
            JOIN agents a ON a.id = ts.agent_id
            """
        )
    )
    op.drop_index("ix_ticket_scans_agent_id", table_name="ticket_scans")
    op.drop_index("ix_ticket_scans_billet_id", table_name="ticket_scans")
    op.drop_table("ticket_scans")
    op.rename_table("ticket_scans_new", "ticket_scans")
    op.create_index("ix_ticket_scans_billet_id", "ticket_scans", ["billet_id"])
    op.create_index("ix_ticket_scans_agent_id", "ticket_scans", ["agent_id"])


def downgrade() -> None:
    op.drop_index("ix_ticket_scans_agent_id", table_name="ticket_scans")
    op.drop_index("ix_ticket_scans_billet_id", table_name="ticket_scans")

    op.create_table(
        "ticket_scans_old",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "billet_id",
            sa.Uuid(),
            sa.ForeignKey("billets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "agent_id",
            sa.Uuid(),
            sa.ForeignKey("utilisateurs.id"),
            nullable=False,
        ),
        sa.Column("result", sa.String(length=30), nullable=False),
        sa.Column(
            "scanned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO ticket_scans_old (id, billet_id, agent_id, result, scanned_at)
            SELECT id, billet_id, agent_id, result, scanned_at
            FROM ticket_scans
            """
        )
    )
    op.drop_table("ticket_scans")
    op.rename_table("ticket_scans_old", "ticket_scans")
    op.create_index("ix_ticket_scans_billet_id", "ticket_scans", ["billet_id"])
    op.create_index("ix_ticket_scans_agent_id", "ticket_scans", ["agent_id"])

    op.drop_index("ix_evenement_agents_agent_id", table_name="evenement_agents")
    op.drop_index("ix_evenement_agents_evenement_id", table_name="evenement_agents")

    op.create_table(
        "evenement_agents_old",
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
    op.execute(
        sa.text(
            """
            INSERT INTO evenement_agents_old (evenement_id, agent_id)
            SELECT evenement_id, agent_id
            FROM evenement_agents
            """
        )
    )
    op.drop_table("evenement_agents")
    op.rename_table("evenement_agents_old", "evenement_agents")
    op.create_index("ix_evenement_agents_evenement_id", "evenement_agents", ["evenement_id"])
    op.create_index("ix_evenement_agents_agent_id", "evenement_agents", ["agent_id"])

    op.drop_table("agents")
    op.drop_table("participants")
    op.drop_table("organisateurs")
    op.drop_table("admins")

