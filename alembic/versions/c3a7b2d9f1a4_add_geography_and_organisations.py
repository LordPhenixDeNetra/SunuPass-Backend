from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c3a7b2d9f1a4"
down_revision = "35061bc46e4f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "countries",
        sa.Column("code", sa.String(length=3), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("calling_code", sa.String(length=10), nullable=False),
    )

    op.create_table(
        "administrative_levels",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("level_order", sa.Integer(), nullable=False),
        sa.Column("country_code", sa.String(length=3), sa.ForeignKey("countries.code", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("country_code", "level_order", name="uq_country_level_order"),
    )
    op.create_index("ix_administrative_levels_country_code", "administrative_levels", ["country_code"])

    op.create_table(
        "administrative_units",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column(
            "level_id",
            sa.Uuid(),
            sa.ForeignKey("administrative_levels.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "parent_id",
            sa.Uuid(),
            sa.ForeignKey("administrative_units.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.UniqueConstraint("parent_id", "name", name="uq_unit_per_parent"),
    )
    op.create_index("ix_administrative_units_level_id", "administrative_units", ["level_id"])
    op.create_index("ix_administrative_units_parent_id", "administrative_units", ["parent_id"])

    op.create_table(
        "organisations",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("nom_organisation", sa.String(length=150), nullable=False),
        sa.Column("nb_employes_min", sa.Integer(), nullable=False),
        sa.Column("nb_employes_max", sa.Integer(), nullable=False),
        sa.Column(
            "pays_code",
            sa.String(length=3),
            sa.ForeignKey("countries.code", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("telephone", sa.String(length=30), nullable=False),
        sa.CheckConstraint("nb_employes_min >= 0", name="ck_organisation_nb_employes_min_nonneg"),
        sa.CheckConstraint("nb_employes_max >= 0", name="ck_organisation_nb_employes_max_nonneg"),
        sa.CheckConstraint("nb_employes_min <= nb_employes_max", name="ck_organisation_nb_employes_range"),
    )
    op.create_index("ix_organisations_nom_organisation", "organisations", ["nom_organisation"])
    op.create_index("ix_organisations_pays_code", "organisations", ["pays_code"])
    op.create_index("ix_organisations_email", "organisations", ["email"])
    op.create_index("ix_organisations_telephone", "organisations", ["telephone"])

    op.add_column("organisateurs", sa.Column("organisation_id", sa.Uuid(), nullable=True))
    op.create_index("ix_organisateurs_organisation_id", "organisateurs", ["organisation_id"])
    op.create_foreign_key(
        "fk_organisateurs_organisation_id_organisations",
        "organisateurs",
        "organisations",
        ["organisation_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_organisateurs_organisation_id_organisations", "organisateurs", type_="foreignkey")
    op.drop_index("ix_organisateurs_organisation_id", table_name="organisateurs")
    op.drop_column("organisateurs", "organisation_id")

    op.drop_index("ix_organisations_telephone", table_name="organisations")
    op.drop_index("ix_organisations_email", table_name="organisations")
    op.drop_index("ix_organisations_pays_code", table_name="organisations")
    op.drop_index("ix_organisations_nom_organisation", table_name="organisations")
    op.drop_table("organisations")

    op.drop_index("ix_administrative_units_parent_id", table_name="administrative_units")
    op.drop_index("ix_administrative_units_level_id", table_name="administrative_units")
    op.drop_table("administrative_units")

    op.drop_index("ix_administrative_levels_country_code", table_name="administrative_levels")
    op.drop_table("administrative_levels")

    op.drop_table("countries")

