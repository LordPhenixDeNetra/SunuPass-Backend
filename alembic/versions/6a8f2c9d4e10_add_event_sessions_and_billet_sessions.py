from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "6a8f2c9d4e10"
down_revision = "2f2c13f7c4a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evenement_id", sa.Uuid(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=True),
        sa.Column("day_index", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint("ends_at > starts_at", name="ck_event_sessions_ends_after_starts"),
        sa.ForeignKeyConstraint(["evenement_id"], ["evenements.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_sessions_evenement_id", "event_sessions", ["evenement_id"], unique=False)
    op.create_index("ix_event_sessions_starts_at", "event_sessions", ["starts_at"], unique=False)
    op.create_index("ix_event_sessions_ends_at", "event_sessions", ["ends_at"], unique=False)

    op.create_table(
        "billet_sessions",
        sa.Column("billet_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["billet_id"], ["billets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["event_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("billet_id", "session_id"),
    )
    op.create_index("ix_billet_sessions_billet_id", "billet_sessions", ["billet_id"], unique=False)
    op.create_index("ix_billet_sessions_session_id", "billet_sessions", ["session_id"], unique=False)

    op.add_column("ticket_scans", sa.Column("session_id", sa.Uuid(), nullable=True))
    op.create_index("ix_ticket_scans_session_id", "ticket_scans", ["session_id"], unique=False)
    op.create_foreign_key(
        "fk_ticket_scans_session_id",
        "ticket_scans",
        "event_sessions",
        ["session_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_ticket_scans_session_id", "ticket_scans", type_="foreignkey")
    op.drop_index("ix_ticket_scans_session_id", table_name="ticket_scans")
    op.drop_column("ticket_scans", "session_id")

    op.drop_index("ix_billet_sessions_session_id", table_name="billet_sessions")
    op.drop_index("ix_billet_sessions_billet_id", table_name="billet_sessions")
    op.drop_table("billet_sessions")

    op.drop_index("ix_event_sessions_ends_at", table_name="event_sessions")
    op.drop_index("ix_event_sessions_starts_at", table_name="event_sessions")
    op.drop_index("ix_event_sessions_evenement_id", table_name="event_sessions")
    op.drop_table("event_sessions")

