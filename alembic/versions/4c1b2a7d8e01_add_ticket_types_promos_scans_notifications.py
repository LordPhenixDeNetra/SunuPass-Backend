from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "4c1b2a7d8e01"
down_revision = "35061bc46e4f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'AGENT'")
        op.execute("ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'REMBOURSE'")
        postgresql.ENUM("PERCENT", "FIXED", name="promo_discount_type").create(bind, checkfirst=True)

    op.add_column("evenements", sa.Column("branding_logo_url", sa.String(length=500), nullable=True))
    op.add_column("evenements", sa.Column("branding_primary_color", sa.String(length=20), nullable=True))

    op.create_table(
        "ticket_types",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evenement_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=150), nullable=False),
        sa.Column("prix", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("quota", sa.Integer(), nullable=False),
        sa.Column("sales_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sales_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
        sa.ForeignKeyConstraint(["evenement_id"], ["evenements.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evenement_id", "code", name="uq_ticket_types_event_code"),
    )
    op.create_index("ix_ticket_types_evenement_id", "ticket_types", ["evenement_id"], unique=False)

    if dialect == "postgresql":
        discount_type_enum = postgresql.ENUM("PERCENT", "FIXED", name="promo_discount_type", create_type=False)
    else:
        discount_type_enum = sa.Enum("PERCENT", "FIXED", name="promo_discount_type")
    op.create_table(
        "promo_codes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evenement_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("discount_type", discount_type_enum, nullable=False),
        sa.Column("value", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_limit", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
        sa.ForeignKeyConstraint(["evenement_id"], ["evenements.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evenement_id", "code", name="uq_promo_codes_event_code"),
    )
    op.create_index("ix_promo_codes_evenement_id", "promo_codes", ["evenement_id"], unique=False)

    op.add_column("billets", sa.Column("ticket_type_id", sa.Uuid(), nullable=True))
    op.add_column("billets", sa.Column("prix_initial", sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column("billets", sa.Column("promo_code_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_billets_ticket_type_id", "billets", "ticket_types", ["ticket_type_id"], ["id"])
    op.create_foreign_key("fk_billets_promo_code_id", "billets", "promo_codes", ["promo_code_id"], ["id"])

    op.create_table(
        "ticket_scans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("billet_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("result", sa.String(length=30), nullable=False),
        sa.Column(
            "scanned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["agent_id"], ["utilisateurs.id"]),
        sa.ForeignKeyConstraint(["billet_id"], ["billets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ticket_scans_billet_id", "ticket_scans", ["billet_id"], unique=False)
    op.create_index("ix_ticket_scans_agent_id", "ticket_scans", ["agent_id"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["utilisateurs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_ticket_scans_agent_id", table_name="ticket_scans")
    op.drop_index("ix_ticket_scans_billet_id", table_name="ticket_scans")
    op.drop_table("ticket_scans")

    op.drop_constraint("fk_billets_promo_code_id", "billets", type_="foreignkey")
    op.drop_constraint("fk_billets_ticket_type_id", "billets", type_="foreignkey")
    op.drop_column("billets", "promo_code_id")
    op.drop_column("billets", "prix_initial")
    op.drop_column("billets", "ticket_type_id")

    op.drop_index("ix_promo_codes_evenement_id", table_name="promo_codes")
    op.drop_table("promo_codes")

    op.drop_index("ix_ticket_types_evenement_id", table_name="ticket_types")
    op.drop_table("ticket_types")

    op.drop_column("evenements", "branding_primary_color")
    op.drop_column("evenements", "branding_logo_url")

    if dialect == "postgresql":
        op.execute("DROP TYPE IF EXISTS promo_discount_type")
