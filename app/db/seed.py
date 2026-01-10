from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_refresh_token,
    hash_password,
    new_jti,
)
from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.models.enums import EventStatus, PaymentStatus, TicketStatus, UserRole
from app.models.event import Evenement
from app.models.payment import Paiement
from app.models.refresh_token import RefreshToken
from app.models.ticket import Billet
from app.models.user import Utilisateur
from app.services.refresh_tokens import revoke_refresh_token


@dataclass(frozen=True)
class SeedResult:
    utilisateurs: int
    evenements: int
    billets: int
    paiements: int
    refresh_tokens: int


def _get_user_by_email(db: Session, email: str) -> Utilisateur | None:
    return db.execute(select(Utilisateur).where(Utilisateur.email == email)).scalar_one_or_none()


def _ensure_user(
    db: Session,
    *,
    email: str,
    nom_complet: str,
    role: UserRole,
    password: str,
    is_active: bool = True,
) -> tuple[Utilisateur, bool]:
    existing = _get_user_by_email(db, email)
    if existing is not None:
        return existing, False

    user = Utilisateur(
        email=email,
        nom_complet=nom_complet,
        role=role,
        hashed_password=hash_password(password),
        is_active=is_active,
    )
    db.add(user)
    db.flush()
    return user, True


def _ensure_event(
    db: Session,
    *,
    organisateur: Utilisateur,
    titre: str,
    description: str | None,
    date_debut: datetime,
    lieu: str | None,
    capacite: int,
    statut: EventStatus,
) -> tuple[Evenement, bool]:
    stmt = select(Evenement).where(
        Evenement.organisateur_id == organisateur.id,
        Evenement.titre == titre,
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing is not None:
        return existing, False

    evt = Evenement(
        organisateur_id=organisateur.id,
        titre=titre,
        description=description,
        date_debut=date_debut,
        lieu=lieu,
        capacite=capacite,
        statut=statut,
    )
    db.add(evt)
    db.flush()
    return evt, True


def _ensure_ticket(
    db: Session,
    *,
    evenement: Evenement,
    participant: Utilisateur,
    type_: str,
    prix,
    statut: TicketStatus,
) -> tuple[Billet, bool]:
    stmt = select(Billet).where(
        Billet.evenement_id == evenement.id,
        Billet.participant_id == participant.id,
        Billet.type == type_,
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing is not None:
        return existing, False

    billet = Billet(
        evenement_id=evenement.id,
        participant_id=participant.id,
        type=type_,
        prix=prix,
        statut=statut,
        qr_code=f"QR-{uuid.uuid4()}",
    )
    db.add(billet)
    db.flush()
    return billet, True


def _ensure_payment(
    db: Session,
    *,
    billet: Billet,
    montant,
    moyen: str,
    statut: PaymentStatus,
    date_paiement: datetime | None,
) -> tuple[Paiement, bool]:
    stmt = select(Paiement).where(Paiement.billet_id == billet.id)
    existing = db.execute(stmt).scalar_one_or_none()
    if existing is not None:
        return existing, False

    paiement = Paiement(
        billet_id=billet.id,
        montant=montant,
        moyen=moyen,
        statut=statut,
        date_paiement=date_paiement,
    )
    db.add(paiement)
    db.flush()
    return paiement, True


def _ensure_refresh_token(
    db: Session,
    *,
    user: Utilisateur,
    revoked: bool,
    expires_at: datetime,
) -> tuple[RefreshToken, bool]:
    stmt = select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked == revoked)
    existing = db.execute(stmt).scalars().first()
    if existing is not None:
        return existing, False

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
        revoke_refresh_token(db, row)
        db.refresh(row)

    return row, True


def seed(db: Session) -> SeedResult:
    now = datetime.now(timezone.utc)
    users_created = 0
    events_created = 0
    tickets_created = 0
    payments_created = 0
    refresh_created = 0

    admin, created = _ensure_user(
        db,
        email="admin@sunupass.local",
        nom_complet="Admin SunuPass",
        role=UserRole.ADMIN,
        password="Admin123!",
    )
    users_created += int(created)

    org1, created = _ensure_user(
        db,
        email="org1@sunupass.local",
        nom_complet="Organisateur 1",
        role=UserRole.ORGANISATEUR,
        password="Org123!",
    )
    users_created += int(created)

    org2, created = _ensure_user(
        db,
        email="org2@sunupass.local",
        nom_complet="Organisateur 2",
        role=UserRole.ORGANISATEUR,
        password="Org123!",
    )
    users_created += int(created)

    participants: list[Utilisateur] = []
    for i in range(1, 5):
        p, created = _ensure_user(
            db,
            email=f"participant{i}@sunupass.local",
            nom_complet=f"Participant {i}",
            role=UserRole.PARTICIPANT,
            password="Pass123!",
        )
        users_created += int(created)
        participants.append(p)

    e1, created = _ensure_event(
        db,
        organisateur=org1,
        titre="Festival SunuPass 2026",
        description="Festival multi-activités",
        date_debut=now + timedelta(days=20),
        lieu="Dakar",
        capacite=500,
        statut=EventStatus.PUBLIE,
    )
    events_created += int(created)

    e2, created = _ensure_event(
        db,
        organisateur=org1,
        titre="Conférence Tech SunuPass",
        description="Conférence sur les systèmes de billetterie",
        date_debut=now + timedelta(days=35),
        lieu="Thiès",
        capacite=250,
        statut=EventStatus.BROUILLON,
    )
    events_created += int(created)

    e3, created = _ensure_event(
        db,
        organisateur=org2,
        titre="Match de gala",
        description="Rencontre sportive",
        date_debut=now + timedelta(days=10),
        lieu="Saint-Louis",
        capacite=300,
        statut=EventStatus.PUBLIE,
    )
    events_created += int(created)

    e4, created = _ensure_event(
        db,
        organisateur=org2,
        titre="Atelier QR Code",
        description="Atelier pratique",
        date_debut=now + timedelta(days=5),
        lieu="Dakar",
        capacite=40,
        statut=EventStatus.TERMINE,
    )
    events_created += int(created)

    from decimal import Decimal

    b11, created = _ensure_ticket(
        db,
        evenement=e1,
        participant=participants[0],
        type_="STANDARD",
        prix=Decimal("5000.00"),
        statut=TicketStatus.PAYE,
    )
    tickets_created += int(created)
    pay, created = _ensure_payment(
        db,
        billet=b11,
        montant=Decimal("5000.00"),
        moyen="WAVE",
        statut=PaymentStatus.SUCCES,
        date_paiement=now - timedelta(days=1),
    )
    payments_created += int(created)

    b12, created = _ensure_ticket(
        db,
        evenement=e1,
        participant=participants[1],
        type_="VIP",
        prix=Decimal("15000.00"),
        statut=TicketStatus.CREE,
    )
    tickets_created += int(created)

    b21, created = _ensure_ticket(
        db,
        evenement=e3,
        participant=participants[2],
        type_="STANDARD",
        prix=Decimal("3000.00"),
        statut=TicketStatus.PAYE,
    )
    tickets_created += int(created)
    pay, created = _ensure_payment(
        db,
        billet=b21,
        montant=Decimal("3000.00"),
        moyen="OM",
        statut=PaymentStatus.EN_ATTENTE,
        date_paiement=None,
    )
    payments_created += int(created)

    b22, created = _ensure_ticket(
        db,
        evenement=e4,
        participant=participants[3],
        type_="STANDARD",
        prix=Decimal("2000.00"),
        statut=TicketStatus.UTILISE,
    )
    tickets_created += int(created)
    pay, created = _ensure_payment(
        db,
        billet=b22,
        montant=Decimal("2000.00"),
        moyen="CASH",
        statut=PaymentStatus.SUCCES,
        date_paiement=now - timedelta(days=7),
    )
    payments_created += int(created)

    rt, created = _ensure_refresh_token(
        db,
        user=admin,
        revoked=False,
        expires_at=now + timedelta(days=get_settings().refresh_token_expire_days),
    )
    refresh_created += int(created)
    rt, created = _ensure_refresh_token(
        db,
        user=admin,
        revoked=True,
        expires_at=now + timedelta(days=get_settings().refresh_token_expire_days),
    )
    refresh_created += int(created)

    return SeedResult(
        utilisateurs=users_created,
        evenements=events_created,
        billets=tickets_created,
        paiements=payments_created,
        refresh_tokens=refresh_created,
    )


def main() -> None:
    with SessionLocal() as db:
        result = seed(db)
        db.commit()
    print(
        f"Seed OK: utilisateurs={result.utilisateurs}, evenements={result.evenements}, billets={result.billets}, "
        f"paiements={result.paiements}, refresh_tokens={result.refresh_tokens}"
    )


if __name__ == "__main__":
    main()

