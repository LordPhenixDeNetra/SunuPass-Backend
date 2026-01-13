from __future__ import annotations

import argparse
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.security import (
    create_refresh_token,
    hash_password,
    new_jti,
)
from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.models.enums import EventStatus, PaymentStatus, PromoDiscountType, TicketStatus, UserRole
from app.models.event import Evenement
from app.models.notification import Notification
from app.models.promo_code import PromoCode
from app.models.payment import Paiement
from app.models.refresh_token import RefreshToken
from app.models.ticket import Billet
from app.models.ticket_scan import TicketScan
from app.models.ticket_type import TicketType
from app.models.user import Admin, Agent, Organisateur, Participant, Utilisateur


@dataclass(frozen=True)
class SeedResult:
    utilisateurs: int
    evenements: int
    ticket_types: int
    promo_codes: int
    billets: int
    paiements: int
    scans: int
    notifications: int
    refresh_tokens: int


def reset_database(db: Session) -> None:
    bind = db.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        table_names = [
            r[0]
            for r in db.execute(
                text(
                    """
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                      AND tablename <> 'alembic_version'
                    """
                )
            ).all()
        ]
        if not table_names:
            return
        tables_csv = ", ".join(f'"{name}"' for name in table_names)
        db.execute(text(f"TRUNCATE TABLE {tables_csv} RESTART IDENTITY CASCADE"))
        db.flush()
        return

    if dialect == "sqlite":
        table_names = [
            r[0]
            for r in db.execute(
                text(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table'
                      AND name NOT LIKE 'sqlite_%'
                      AND name <> 'alembic_version'
                    """
                )
            ).all()
        ]
        if not table_names:
            return
        db.execute(text("PRAGMA foreign_keys=OFF"))
        for name in table_names:
            db.execute(text(f'DELETE FROM "{name}"'))
        db.execute(text("PRAGMA foreign_keys=ON"))
        db.flush()
        return

    raise RuntimeError(f"Unsupported database dialect: {dialect}")


def _create_user(
    db: Session,
    *,
    email: str,
    nom_complet: str,
    role: UserRole,
    password: str,
    is_active: bool = True,
) -> Utilisateur:
    user_cls: type[Utilisateur]
    if role == UserRole.ADMIN:
        user_cls = Admin
    elif role == UserRole.ORGANISATEUR:
        user_cls = Organisateur
    elif role == UserRole.AGENT:
        user_cls = Agent
    else:
        user_cls = Participant

    user = user_cls(
        email=email,
        nom_complet=nom_complet,
        hashed_password=hash_password(password),
        is_active=is_active,
    )
    db.add(user)
    db.flush()
    return user


def _create_event(
    db: Session,
    *,
    organisateur: Utilisateur,
    titre: str,
    description: str | None,
    date_debut: datetime,
    lieu: str | None,
    capacite: int,
    statut: EventStatus,
    branding_logo_url: str | None = None,
    branding_primary_color: str | None = None,
    agents: list[Utilisateur] | None = None,
) -> Evenement:
    evt = Evenement(
        organisateur_id=organisateur.id,
        titre=titre,
        description=description,
        date_debut=date_debut,
        lieu=lieu,
        capacite=capacite,
        statut=statut,
        branding_logo_url=branding_logo_url,
        branding_primary_color=branding_primary_color,
    )
    if agents:
        evt.agents = list(agents)
    db.add(evt)
    db.flush()
    return evt


def _create_ticket_type(
    db: Session,
    *,
    evenement: Evenement,
    code: str,
    label: str,
    prix: Decimal,
    quota: int,
    sales_start: datetime | None = None,
    sales_end: datetime | None = None,
    is_active: bool = True,
) -> TicketType:
    row = TicketType(
        evenement_id=evenement.id,
        code=code,
        label=label,
        prix=prix,
        quota=quota,
        sales_start=sales_start,
        sales_end=sales_end,
        is_active=is_active,
    )
    db.add(row)
    db.flush()
    return row


def _create_promo_code(
    db: Session,
    *,
    evenement: Evenement,
    code: str,
    discount_type: PromoDiscountType,
    value: Decimal,
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
    usage_limit: int | None = None,
    is_active: bool = True,
) -> PromoCode:
    row = PromoCode(
        evenement_id=evenement.id,
        code=code,
        discount_type=discount_type,
        value=value,
        starts_at=starts_at,
        ends_at=ends_at,
        usage_limit=usage_limit,
        used_count=0,
        is_active=is_active,
    )
    db.add(row)
    db.flush()
    return row


def _compute_discounted_price(
    *,
    base_price: Decimal,
    promo: PromoCode | None,
) -> Decimal:
    if promo is None:
        return Decimal(str(base_price)).quantize(Decimal("0.01"))

    price = Decimal(str(base_price)).quantize(Decimal("0.01"))
    if promo.discount_type == PromoDiscountType.PERCENT:
        price = (price * (Decimal("100") - promo.value) / Decimal("100")).quantize(Decimal("0.01"))
    else:
        price = (price - promo.value).quantize(Decimal("0.01"))
    if price < 0:
        return Decimal("0.00")
    return price


def _create_ticket(
    db: Session,
    *,
    evenement: Evenement,
    ticket_type: TicketType,
    participant: Utilisateur | None,
    guest_email: str | None,
    guest_nom_complet: str | None,
    guest_phone: str | None,
    promo: PromoCode | None,
    statut: TicketStatus,
    qr_code: str,
) -> Billet:
    base_price = Decimal(str(ticket_type.prix)).quantize(Decimal("0.01"))
    final_price = _compute_discounted_price(base_price=base_price, promo=promo)
    billet = Billet(
        evenement_id=evenement.id,
        participant_id=None if participant is None else participant.id,
        guest_email=guest_email,
        guest_nom_complet=guest_nom_complet,
        guest_phone=guest_phone,
        ticket_type_id=ticket_type.id,
        type=ticket_type.code,
        prix_initial=base_price,
        prix=final_price,
        qr_code=qr_code,
        promo_code_id=None if promo is None else promo.id,
        statut=statut,
    )
    db.add(billet)
    db.flush()
    return billet


def _create_payment(
    db: Session,
    *,
    billet: Billet,
    montant: Decimal,
    moyen: str,
    statut: PaymentStatus,
    date_paiement: datetime | None,
) -> Paiement:
    paiement = Paiement(
        billet_id=billet.id,
        montant=montant,
        moyen=moyen,
        statut=statut,
        date_paiement=date_paiement,
    )
    db.add(paiement)
    db.flush()
    return paiement


def _create_scan(
    db: Session,
    *,
    billet: Billet,
    agent: Utilisateur,
    result: str,
) -> TicketScan:
    row = TicketScan(billet_id=billet.id, agent_id=agent.id, result=result)
    db.add(row)
    db.flush()
    return row


def _create_notification(
    db: Session,
    *,
    user: Utilisateur,
    type_: str,
    title: str,
    body: str,
) -> Notification:
    row = Notification(user_id=user.id, type=type_, title=title, body=body, is_read=False)
    db.add(row)
    db.flush()
    return row


def _create_refresh_token(
    db: Session,
    *,
    user: Utilisateur,
    revoked: bool,
    expires_at: datetime,
) -> RefreshToken:
    jti = new_jti()
    refresh_token = create_refresh_token(subject=str(user.id), jti=jti)
    row = RefreshToken(
        user_id=user.id,
        jti=jti,
        token_hash="",
        expires_at=expires_at,
        revoked=False,
    )
    from app.core.security import hash_token

    row.token_hash = hash_token(refresh_token)
    db.add(row)
    db.flush()

    if revoked:
        row.revoked = True
        db.add(row)
        db.flush()

    return row


def seed(db: Session, *, reset: bool = True) -> SeedResult:
    now = datetime.now(timezone.utc)
    if reset:
        reset_database(db)

    admin = _create_user(
        db,
        email="admin@sunupass.local",
        nom_complet="Admin SunuPass",
        role=UserRole.ADMIN,
        password="Admin123!",
    )
    org1 = _create_user(
        db,
        email="org1@sunupass.local",
        nom_complet="Organisateur 1",
        role=UserRole.ORGANISATEUR,
        password="Org123!",
    )
    org2 = _create_user(
        db,
        email="org2@sunupass.local",
        nom_complet="Organisateur 2",
        role=UserRole.ORGANISATEUR,
        password="Org123!",
    )
    agent1 = _create_user(
        db,
        email="agent1@sunupass.local",
        nom_complet="Agent 1",
        role=UserRole.AGENT,
        password="Agent123!",
    )
    agent2 = _create_user(
        db,
        email="agent2@sunupass.local",
        nom_complet="Agent 2",
        role=UserRole.AGENT,
        password="Agent123!",
    )

    participants: list[Utilisateur] = [
        _create_user(
            db,
            email=f"participant{i}@sunupass.local",
            nom_complet=f"Participant {i}",
            role=UserRole.PARTICIPANT,
            password="Pass123!",
        )
        for i in range(1, 5)
    ]

    e1 = _create_event(
        db,
        organisateur=org1,
        titre="Festival SunuPass 2026",
        description="Festival multi-activités",
        date_debut=now + timedelta(days=20),
        lieu="Dakar",
        capacite=500,
        statut=EventStatus.PUBLIE,
        branding_logo_url="https://example.com/logo-festival.png",
        branding_primary_color="#FF6600",
        agents=[agent1, agent2],
    )
    e2 = _create_event(
        db,
        organisateur=org1,
        titre="Conférence Tech SunuPass",
        description="Conférence sur les systèmes de billetterie",
        date_debut=now + timedelta(days=35),
        lieu="Thiès",
        capacite=250,
        statut=EventStatus.BROUILLON,
        agents=[agent2],
    )
    e3 = _create_event(
        db,
        organisateur=org2,
        titre="Match de gala",
        description="Rencontre sportive",
        date_debut=now + timedelta(days=10),
        lieu="Saint-Louis",
        capacite=300,
        statut=EventStatus.PUBLIE,
        branding_logo_url="https://example.com/logo-match.png",
        branding_primary_color="#0066FF",
        agents=[agent1],
    )
    e4 = _create_event(
        db,
        organisateur=org2,
        titre="Atelier QR Code",
        description="Atelier pratique",
        date_debut=now - timedelta(days=5),
        lieu="Dakar",
        capacite=40,
        statut=EventStatus.TERMINE,
        agents=[agent1],
    )

    e1_standard = _create_ticket_type(
        db,
        evenement=e1,
        code="STANDARD",
        label="Pass Standard",
        prix=Decimal("5000.00"),
        quota=0,
        sales_start=now - timedelta(days=10),
        sales_end=e1.date_debut - timedelta(days=1),
        is_active=True,
    )
    e1_vip = _create_ticket_type(
        db,
        evenement=e1,
        code="VIP",
        label="Pass VIP",
        prix=Decimal("15000.00"),
        quota=50,
        sales_start=now - timedelta(days=10),
        sales_end=e1.date_debut - timedelta(days=1),
        is_active=True,
    )
    e3_standard = _create_ticket_type(
        db,
        evenement=e3,
        code="STANDARD",
        label="Billet Standard",
        prix=Decimal("3000.00"),
        quota=0,
        sales_start=now - timedelta(days=10),
        sales_end=e3.date_debut - timedelta(days=1),
        is_active=True,
    )
    e3_fan = _create_ticket_type(
        db,
        evenement=e3,
        code="FAN",
        label="Billet Fan",
        prix=Decimal("1000.00"),
        quota=200,
        sales_start=now - timedelta(days=10),
        sales_end=e3.date_debut - timedelta(days=1),
        is_active=True,
    )
    e4_workshop = _create_ticket_type(
        db,
        evenement=e4,
        code="WORKSHOP",
        label="Billet Atelier",
        prix=Decimal("2000.00"),
        quota=40,
        sales_start=now - timedelta(days=60),
        sales_end=e4.date_debut - timedelta(days=1),
        is_active=False,
    )

    e1_early10 = _create_promo_code(
        db,
        evenement=e1,
        code="EARLY10",
        discount_type=PromoDiscountType.PERCENT,
        value=Decimal("10.00"),
        starts_at=now - timedelta(days=30),
        ends_at=now + timedelta(days=5),
        usage_limit=500,
        is_active=True,
    )
    e3_fix500 = _create_promo_code(
        db,
        evenement=e3,
        code="FIX500",
        discount_type=PromoDiscountType.FIXED,
        value=Decimal("500.00"),
        starts_at=now - timedelta(days=15),
        ends_at=now + timedelta(days=7),
        usage_limit=100,
        is_active=True,
    )

    b11 = _create_ticket(
        db,
        evenement=e1,
        ticket_type=e1_standard,
        participant=participants[0],
        guest_email=None,
        guest_nom_complet=None,
        guest_phone=None,
        promo=e1_early10,
        statut=TicketStatus.PAYE,
        qr_code=f"SEED-{e1.id.hex[:8]}-participant1-STANDARD",
    )
    _create_payment(
        db,
        billet=b11,
        montant=Decimal(str(b11.prix)),
        moyen="WAVE",
        statut=PaymentStatus.SUCCES,
        date_paiement=now - timedelta(days=1),
    )
    _create_notification(
        db,
        user=participants[0],
        type_="PAYMENT_SUCCESS",
        title="Paiement confirmé",
        body=f"Votre paiement pour le billet {b11.type} est confirmé.",
    )

    b12 = _create_ticket(
        db,
        evenement=e1,
        ticket_type=e1_vip,
        participant=participants[1],
        guest_email=None,
        guest_nom_complet=None,
        guest_phone=None,
        promo=None,
        statut=TicketStatus.CREE,
        qr_code=f"SEED-{e1.id.hex[:8]}-participant2-VIP",
    )
    _create_notification(
        db,
        user=participants[1],
        type_="TICKET_CREATED",
        title="Billet créé",
        body=f"Votre billet {b12.type} a été créé pour l’événement {e1.titre}.",
    )

    b21 = _create_ticket(
        db,
        evenement=e3,
        ticket_type=e3_standard,
        participant=participants[2],
        guest_email=None,
        guest_nom_complet=None,
        guest_phone=None,
        promo=e3_fix500,
        statut=TicketStatus.CREE,
        qr_code=f"SEED-{e3.id.hex[:8]}-participant3-STANDARD",
    )
    _create_payment(
        db,
        billet=b21,
        montant=Decimal(str(b21.prix)),
        moyen="OM",
        statut=PaymentStatus.EN_ATTENTE,
        date_paiement=None,
    )

    b22 = _create_ticket(
        db,
        evenement=e4,
        ticket_type=e4_workshop,
        participant=participants[3],
        guest_email=None,
        guest_nom_complet=None,
        guest_phone=None,
        promo=None,
        statut=TicketStatus.UTILISE,
        qr_code=f"SEED-{e4.id.hex[:8]}-participant4-WORKSHOP",
    )
    _create_payment(
        db,
        billet=b22,
        montant=Decimal(str(b22.prix)),
        moyen="CASH",
        statut=PaymentStatus.SUCCES,
        date_paiement=now - timedelta(days=7),
    )
    _create_scan(db, billet=b22, agent=agent1, result="OK")
    _create_notification(
        db,
        user=participants[3],
        type_="TICKET_USED",
        title="Entrée validée",
        body=f"Votre billet {b22.type} a été validé à l’entrée.",
    )

    _create_ticket(
        db,
        evenement=e3,
        ticket_type=e3_fan,
        participant=None,
        guest_email="guest@example.com",
        guest_nom_complet="Guest Buyer",
        guest_phone="+221770000000",
        promo=None,
        statut=TicketStatus.CREE,
        qr_code=f"SEED-{e3.id.hex[:8]}-guest-FAN",
    )

    expires_at = now + timedelta(days=get_settings().refresh_token_expire_days)
    _create_refresh_token(db, user=admin, revoked=False, expires_at=expires_at)
    _create_refresh_token(db, user=admin, revoked=True, expires_at=expires_at)

    promos = db.execute(select(PromoCode)).scalars().all()
    for promo in promos:
        promo.used_count = int(
            db.execute(select(func.count()).select_from(Billet).where(Billet.promo_code_id == promo.id)).scalar_one()
        )
        db.add(promo)
    db.flush()

    return SeedResult(
        utilisateurs=1 + 2 + 2 + len(participants),
        evenements=4,
        ticket_types=5,
        promo_codes=2,
        billets=5,
        paiements=3,
        scans=1,
        notifications=3,
        refresh_tokens=2,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    with SessionLocal() as db:
        result = seed(db, reset=args.reset)
        db.commit()
    print(
        "Seed OK: utilisateurs="
        f"{result.utilisateurs}, evenements={result.evenements}, ticket_types={result.ticket_types}, "
        f"promo_codes={result.promo_codes}, billets={result.billets}, paiements={result.paiements}, "
        f"scans={result.scans}, notifications={result.notifications}, refresh_tokens={result.refresh_tokens}"
    )


if __name__ == "__main__":
    main()
