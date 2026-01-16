from __future__ import annotations

import argparse
import random
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
from app.models.event import Evenement, EventSession
from app.models.geography import AdministrativeLevel, AdministrativeUnit, Country
from app.models.notification import Notification
from app.models.organisation import Organisation
from app.models.promo_code import PromoCode
from app.models.payment import Paiement
from app.models.refresh_token import RefreshToken
from app.models.ticket import Billet
from app.models.ticket_scan import TicketScan
from app.models.ticket_type import TicketType
from app.models.user import Admin, Agent, Organisateur, Participant, Utilisateur


@dataclass(frozen=True)
class SeedResult:
    countries: int
    administrative_levels: int
    administrative_units: int
    organisations: int
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
        id=uuid.uuid4(),
        email=email,
        nom_complet=nom_complet,
        hashed_password=hash_password(password),
        is_active=is_active,
    )
    db.add(user)
    return user


def _create_country(
    db: Session,
    *,
    code: str,
    name: str,
    calling_code: str,
    flag_svg: str | None = None,
) -> Country:
    row = Country(code=code, name=name, calling_code=calling_code, flag_svg=flag_svg)
    db.add(row)
    return row


def _create_administrative_level(
    db: Session,
    *,
    country: Country,
    name: str,
    level_order: int,
) -> AdministrativeLevel:
    row = AdministrativeLevel(
        id=uuid.uuid4(),
        country_code=country.code,
        name=name,
        level_order=level_order,
    )
    db.add(row)
    return row


def _create_administrative_unit(
    db: Session,
    *,
    level: AdministrativeLevel,
    name: str,
    code: str | None = None,
    parent: AdministrativeUnit | None = None,
    latitude: Decimal | None = None,
    longitude: Decimal | None = None,
) -> AdministrativeUnit:
    row = AdministrativeUnit(
        id=uuid.uuid4(),
        level_id=level.id,
        name=name,
        code=code,
        parent_id=None if parent is None else parent.id,
        latitude=latitude,
        longitude=longitude,
    )
    db.add(row)
    return row


def _create_organisation(
    db: Session,
    *,
    nom_organisation: str,
    nb_employes_min: int,
    nb_employes_max: int,
    pays: Country,
    email: str,
    telephone: str,
) -> Organisation:
    row = Organisation(
        id=uuid.uuid4(),
        nom_organisation=nom_organisation,
        nb_employes_min=nb_employes_min,
        nb_employes_max=nb_employes_max,
        pays_code=pays.code,
        email=email,
        telephone=telephone,
    )
    db.add(row)
    return row


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
        id=uuid.uuid4(),
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
    return evt


def _create_event_session(
    db: Session,
    *,
    evenement: Evenement,
    starts_at: datetime,
    ends_at: datetime,
    label: str | None,
    day_index: int | None,
) -> EventSession:
    row = EventSession(
        id=uuid.uuid4(),
        evenement=evenement,
        starts_at=starts_at,
        ends_at=ends_at,
        label=label,
        day_index=day_index,
    )
    db.add(row)
    return row


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
        id=uuid.uuid4(),
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
        id=uuid.uuid4(),
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
        id=uuid.uuid4(),
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
    if evenement.sessions:
        billet.sessions = list(evenement.sessions)
    db.add(billet)
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
        id=uuid.uuid4(),
        billet_id=billet.id,
        montant=montant,
        moyen=moyen,
        statut=statut,
        date_paiement=date_paiement,
    )
    db.add(paiement)
    return paiement


def _create_scan(
    db: Session,
    *,
    billet: Billet,
    agent: Utilisateur,
    session_id: uuid.UUID | None,
    result: str,
) -> TicketScan:
    row = TicketScan(
        id=uuid.uuid4(),
        billet_id=billet.id,
        agent_id=agent.id,
        session_id=session_id,
        result=result,
    )
    db.add(row)
    return row


def _create_notification(
    db: Session,
    *,
    user: Utilisateur,
    type_: str,
    title: str,
    body: str,
) -> Notification:
    row = Notification(
        id=uuid.uuid4(),
        user_id=user.id,
        type=type_,
        title=title,
        body=body,
        is_read=False,
    )
    db.add(row)
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
        id=uuid.uuid4(),
        user_id=user.id,
        jti=jti,
        token_hash="",
        expires_at=expires_at,
        revoked=revoked,
    )
    from app.core.security import hash_token

    row.token_hash = hash_token(refresh_token)
    db.add(row)
    return row


def seed(db: Session, *, reset: bool = True) -> SeedResult:
    now = datetime.now(timezone.utc)
    if reset:
        reset_database(db)
        db.commit()

    sen = _create_country(
        db,
        code="SEN",
        name="Sénégal",
        calling_code="+221",
        flag_svg="<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 3 2'><rect width='1' height='2' fill='#00853F'/><rect x='1' width='1' height='2' fill='#FDEF42'/><rect x='2' width='1' height='2' fill='#E31B23'/></svg>",
    )
    gmb = _create_country(
        db,
        code="GMB",
        name="Gambie",
        calling_code="+220",
        flag_svg="<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 3 2'><rect width='3' height='2' fill='#fff'/><rect width='3' height='0.6' y='0' fill='#ce1126'/><rect width='3' height='0.2' y='0.7' fill='#0c1c8c'/><rect width='3' height='0.6' y='1.4' fill='#3a7728'/></svg>",
    )

    sen_region = _create_administrative_level(db, country=sen, name="Région", level_order=1)
    sen_dept = _create_administrative_level(db, country=sen, name="Département", level_order=2)
    sen_commune = _create_administrative_level(db, country=sen, name="Commune", level_order=3)

    dakar_region = _create_administrative_unit(
        db,
        level=sen_region,
        name="Dakar",
        code="SN-DK",
        latitude=Decimal("14.692778"),
        longitude=Decimal("-17.446667"),
    )
    thies_region = _create_administrative_unit(
        db,
        level=sen_region,
        name="Thiès",
        code="SN-TH",
        latitude=Decimal("14.791000"),
        longitude=Decimal("-16.925000"),
    )
    stl_region = _create_administrative_unit(
        db,
        level=sen_region,
        name="Saint-Louis",
        code="SN-SL",
        latitude=Decimal("16.017000"),
        longitude=Decimal("-16.489000"),
    )

    dakar_dept = _create_administrative_unit(db, level=sen_dept, name="Dakar", parent=dakar_region)
    pikine_dept = _create_administrative_unit(db, level=sen_dept, name="Pikine", parent=dakar_region)
    thies_dept = _create_administrative_unit(db, level=sen_dept, name="Thiès", parent=thies_region)
    stl_dept = _create_administrative_unit(db, level=sen_dept, name="Saint-Louis", parent=stl_region)

    _create_administrative_unit(db, level=sen_commune, name="Plateau", parent=dakar_dept)
    _create_administrative_unit(db, level=sen_commune, name="Yoff", parent=dakar_dept)
    _create_administrative_unit(db, level=sen_commune, name="Pikine Est", parent=pikine_dept)
    _create_administrative_unit(db, level=sen_commune, name="Tivaouane", parent=thies_dept)
    _create_administrative_unit(db, level=sen_commune, name="Mboro", parent=thies_dept)
    _create_administrative_unit(db, level=sen_commune, name="Sor", parent=stl_dept)

    gmb_region = _create_administrative_level(db, country=gmb, name="Region", level_order=1)
    gmb_district = _create_administrative_level(db, country=gmb, name="District", level_order=2)
    brc = _create_administrative_unit(db, level=gmb_region, name="Banjul", code="GM-BJ")
    _create_administrative_unit(db, level=gmb_district, name="Banjul", parent=brc)

    organisations: list[Organisation] = [
        _create_organisation(
            db,
            nom_organisation="Sunu Events",
            nb_employes_min=10,
            nb_employes_max=50,
            pays=sen,
            email="contact@sunuevents.local",
            telephone="+221770001001",
        ),
        _create_organisation(
            db,
            nom_organisation="Baobab Prod",
            nb_employes_min=1,
            nb_employes_max=10,
            pays=sen,
            email="hello@baobabprod.local",
            telephone="+221770001002",
        ),
        _create_organisation(
            db,
            nom_organisation="Teranga Sport",
            nb_employes_min=20,
            nb_employes_max=200,
            pays=sen,
            email="info@terangasport.local",
            telephone="+221770001003",
        ),
        _create_organisation(
            db,
            nom_organisation="Gambia Live",
            nb_employes_min=5,
            nb_employes_max=30,
            pays=gmb,
            email="support@gambialive.local",
            telephone="+2203300101",
        ),
    ]

    admin = _create_user(
        db,
        email="admin@sunupass.local",
        nom_complet="Admin SunuPass",
        role=UserRole.ADMIN,
        password="Admin123!",
    )
    organisateurs: list[Organisateur] = [
        _create_user(
            db,
            email=f"org{i}@sunupass.local",
            nom_complet=f"Organisateur {i}",
            role=UserRole.ORGANISATEUR,
            password="Org123!",
        )
        for i in range(1, 11)
    ]
    for idx, orga in enumerate(organisateurs):
        orga.organisation_id = organisations[idx % len(organisations)].id
        db.add(orga)
    db.flush()

    agents: list[Agent] = [
        _create_user(
            db,
            email=f"agent{i}@sunupass.local",
            nom_complet=f"Agent {i}",
            role=UserRole.AGENT,
            password="Agent123!",
        )
        for i in range(1, 13)
    ]
    participants: list[Participant] = [
        _create_user(
            db,
            email=f"participant{i}@sunupass.local",
            nom_complet=f"Participant {i}",
            role=UserRole.PARTICIPANT,
            password="Pass123!",
        )
        for i in range(1, 121)
    ]

    published_events: list[Evenement] = []
    ended_events: list[Evenement] = []
    draft_events: list[Evenement] = []

    event_specs = [
        ("Festival SunuPass 2026", "Festival multi-activités", "Dakar", 1200, EventStatus.PUBLIE, "#FF6600"),
        ("Conférence Tech SunuPass", "Conférence billetterie & paiement", "Thiès", 400, EventStatus.PUBLIE, "#111827"),
        ("Match de gala", "Rencontre sportive", "Saint-Louis", 800, EventStatus.PUBLIE, "#0066FF"),
        ("Atelier QR Code", "Atelier pratique", "Dakar", 60, EventStatus.TERMINE, "#10B981"),
        ("Salon Culture", "Expo et rencontres", "Dakar", 900, EventStatus.PUBLIE, "#7C3AED"),
        ("Meetup SaaS", "Réseautage & démos", "Thiès", 200, EventStatus.BROUILLON, "#F59E0B"),
        ("Concert Live", "Show musical", "Dakar", 1500, EventStatus.PUBLIE, "#EF4444"),
        ("Course Urbaine", "Sport & santé", "Saint-Louis", 500, EventStatus.TERMINE, "#22C55E"),
        ("Hackathon", "48h de création", "Dakar", 350, EventStatus.PUBLIE, "#0EA5E9"),
        ("Forum Emploi", "Recrutement & coaching", "Thiès", 600, EventStatus.BROUILLON, "#64748B"),
        ("Soirée Networking", "Business & partenaires", "Dakar", 300, EventStatus.PUBLIE, "#1F2937"),
        ("Projection Plein Air", "Cinéma sous les étoiles", "Saint-Louis", 250, EventStatus.TERMINE, "#A855F7"),
    ]

    for idx, (titre, description, lieu, capacite, statut, color) in enumerate(event_specs, start=1):
        organisateur = organisateurs[(idx - 1) % len(organisateurs)]
        if statut == EventStatus.TERMINE:
            date_debut = now - timedelta(days=10 + idx)
        elif statut == EventStatus.BROUILLON:
            date_debut = now + timedelta(days=45 + idx)
        else:
            date_debut = now + timedelta(days=7 + idx * 3)

        selected_agents = [agents[(idx - 1) % len(agents)], agents[idx % len(agents)]]
        evt = _create_event(
            db,
            organisateur=organisateur,
            titre=titre,
            description=description,
            date_debut=date_debut,
            lieu=lieu,
            capacite=capacite,
            statut=statut,
            branding_logo_url=f"https://example.com/logo-{idx}.png",
            branding_primary_color=color,
            agents=selected_agents,
        )
        if statut == EventStatus.PUBLIE:
            published_events.append(evt)
        elif statut == EventStatus.TERMINE:
            ended_events.append(evt)
        else:
            draft_events.append(evt)

    festival = next((e for e in published_events if e.titre == "Festival SunuPass 2026"), None)
    if festival is not None:
        for i in range(5):
            starts_at = festival.date_debut + timedelta(days=i)
            ends_at = starts_at + timedelta(hours=10)
            _create_event_session(
                db,
                evenement=festival,
                starts_at=starts_at,
                ends_at=ends_at,
                label=f"Jour {i + 1}",
                day_index=i + 1,
            )

    hackathon = next((e for e in published_events if e.titre == "Hackathon"), None)
    if hackathon is not None:
        for i in range(2):
            starts_at = hackathon.date_debut + timedelta(days=i)
            ends_at = starts_at + timedelta(hours=12)
            _create_event_session(
                db,
                evenement=hackathon,
                starts_at=starts_at,
                ends_at=ends_at,
                label=f"Jour {i + 1}",
                day_index=i + 1,
            )

    def _add_standard_stack(evenement: Evenement, *, base_price: Decimal) -> dict[str, TicketType]:
        standard = _create_ticket_type(
            db,
            evenement=evenement,
            code="STANDARD",
            label="Standard",
            prix=base_price,
            quota=0,
            sales_start=now - timedelta(days=30),
            sales_end=evenement.date_debut - timedelta(days=1),
            is_active=True,
        )
        vip = _create_ticket_type(
            db,
            evenement=evenement,
            code="VIP",
            label="VIP",
            prix=(base_price * Decimal("3")).quantize(Decimal("0.01")),
            quota=max(10, evenement.capacite // 20),
            sales_start=now - timedelta(days=30),
            sales_end=evenement.date_debut - timedelta(days=1),
            is_active=True,
        )
        student = _create_ticket_type(
            db,
            evenement=evenement,
            code="STUDENT",
            label="Étudiant",
            prix=(base_price * Decimal("0.6")).quantize(Decimal("0.01")),
            quota=max(20, evenement.capacite // 10),
            sales_start=now - timedelta(days=30),
            sales_end=evenement.date_debut - timedelta(days=2),
            is_active=True,
        )
        return {"STANDARD": standard, "VIP": vip, "STUDENT": student}

    for idx, evt in enumerate(published_events + ended_events, start=1):
        prices = {
            "Dakar": Decimal("5000.00"),
            "Thiès": Decimal("3000.00"),
            "Saint-Louis": Decimal("2500.00"),
        }
        base_price = prices.get(evt.lieu or "", Decimal("4000.00"))
        types_map = _add_standard_stack(evt, base_price=base_price)
        promo = _create_promo_code(
            db,
            evenement=evt,
            code=f"EARLY{idx:02d}",
            discount_type=PromoDiscountType.PERCENT,
            value=Decimal("10.00"),
            starts_at=now - timedelta(days=45),
            ends_at=min(now + timedelta(days=10), evt.date_debut - timedelta(days=3)),
            usage_limit=evt.capacite,
            is_active=True,
        )
        promo2 = _create_promo_code(
            db,
            evenement=evt,
            code=f"FIX{idx:02d}",
            discount_type=PromoDiscountType.FIXED,
            value=(base_price * Decimal("0.1")).quantize(Decimal("0.01")),
            starts_at=now - timedelta(days=10),
            ends_at=evt.date_debut - timedelta(days=1),
            usage_limit=max(50, evt.capacite // 5),
            is_active=True,
        )

        buyer_count = min(80 + idx * 5, max(35, evt.capacite // 5))
        billets_for_event: list[Billet] = []
        for j in range(buyer_count):
            participant = participants[(idx * 7 + j) % len(participants)]
            selected_type = types_map["STANDARD"] if j % 5 else types_map["VIP"]
            selected_promo = promo if j % 3 == 0 else (promo2 if j % 7 == 0 else None)

            if evt in ended_events and j % 4 == 0:
                statut = TicketStatus.UTILISE
            elif j % 3 == 0:
                statut = TicketStatus.PAYE
            elif j % 11 == 0:
                statut = TicketStatus.ANNULE
            else:
                statut = TicketStatus.CREE

            qr = f"SEED-{evt.id.hex[:10]}-{j:04d}-{selected_type.code}"
            billet = _create_ticket(
                db,
                evenement=evt,
                ticket_type=selected_type,
                participant=participant,
                guest_email=None,
                guest_nom_complet=None,
                guest_phone=None,
                promo=selected_promo,
                statut=statut,
                qr_code=qr,
            )
            billets_for_event.append(billet)

            if statut in {TicketStatus.PAYE, TicketStatus.UTILISE}:
                _create_payment(
                    db,
                    billet=billet,
                    montant=Decimal(str(billet.prix)),
                    moyen="WAVE" if j % 2 == 0 else "OM",
                    statut=PaymentStatus.SUCCES,
                    date_paiement=now - timedelta(days=1 + (j % 9)),
                )
                _create_notification(
                    db,
                    user=participant,
                    type_="PAYMENT_SUCCESS",
                    title="Paiement confirmé",
                    body=f"Paiement confirmé pour {evt.titre} ({selected_type.label}).",
                )
            elif statut == TicketStatus.CREE:
                _create_notification(
                    db,
                    user=participant,
                    type_="TICKET_CREATED",
                    title="Billet créé",
                    body=f"Billet {selected_type.label} créé pour {evt.titre}.",
                )
            elif statut == TicketStatus.ANNULE:
                _create_payment(
                    db,
                    billet=billet,
                    montant=Decimal(str(billet.prix)),
                    moyen="OM",
                    statut=PaymentStatus.ECHEC,
                    date_paiement=None,
                )
                _create_notification(
                    db,
                    user=participant,
                    type_="PAYMENT_FAILED",
                    title="Paiement échoué",
                    body=f"Paiement échoué pour {evt.titre}.",
                )

            if statut == TicketStatus.UTILISE:
                agent = agents[(idx + j) % len(agents)]
                _create_scan(
                    db,
                    billet=billet,
                    agent=agent,
                    session_id=None if not billet.session_ids else billet.session_ids[0],
                    result="OK",
                )
                _create_notification(
                    db,
                    user=participant,
                    type_="TICKET_USED",
                    title="Entrée validée",
                    body=f"Entrée validée pour {evt.titre}.",
                )

        if evt.sessions:
            scan_agent = evt.agents[0] if evt.agents else agents[idx % len(agents)]
            scannable_billets = [b for b in billets_for_event if b.statut in {TicketStatus.PAYE, TicketStatus.UTILISE}]
            scannable_billets.sort(key=lambda b: b.created_at or now)
            for b in scannable_billets[:10]:
                if b.statut != TicketStatus.UTILISE:
                    b.statut = TicketStatus.UTILISE
                    db.add(b)
                for s in evt.sessions:
                    _create_scan(
                        db,
                        billet=b,
                        agent=scan_agent,
                        session_id=s.id,
                        result="OK",
                    )

        guest_count = min(10, max(3, evt.capacite // 50))
        for k in range(guest_count):
            selected_type = types_map["STUDENT"] if k % 2 else types_map["STANDARD"]
            qr = f"SEED-{evt.id.hex[:10]}-G{k:03d}-{selected_type.code}"
            billet = _create_ticket(
                db,
                evenement=evt,
                ticket_type=selected_type,
                participant=None,
                guest_email=f"guest{k}@example.com",
                guest_nom_complet=f"Guest {k}",
                guest_phone="+221770000000",
                promo=None,
                statut=TicketStatus.CREE,
                qr_code=qr,
            )

        db.flush()

    evt = _create_event(
        db,
        organisateur=organisateurs[0],
        titre="Banjul Music Night",
        description="Concert en Gambie",
        date_debut=now + timedelta(days=25),
        lieu="Banjul",
        capacite=400,
        statut=EventStatus.PUBLIE,
        branding_logo_url="https://example.com/logo-gm-1.png",
        branding_primary_color="#0F766E",
        agents=[agents[0]],
    )
    published_events.append(evt)
    banjul_standard = _create_ticket_type(
        db,
        evenement=evt,
        code="STANDARD",
        label="Standard",
        prix=Decimal("3500.00"),
        quota=0,
        sales_start=now - timedelta(days=15),
        sales_end=evt.date_debut - timedelta(days=1),
        is_active=True,
    )
    promo = _create_promo_code(
        db,
        evenement=evt,
        code="GMB10",
        discount_type=PromoDiscountType.PERCENT,
        value=Decimal("10.00"),
        starts_at=now - timedelta(days=10),
        ends_at=evt.date_debut - timedelta(days=2),
        usage_limit=200,
        is_active=True,
    )
    for j in range(80):
        participant = participants[(j * 5) % len(participants)]
        qr = f"SEED-{evt.id.hex[:10]}-{j:04d}-STANDARD"
        billet = _create_ticket(
            db,
            evenement=evt,
            ticket_type=banjul_standard,
            participant=participant,
            guest_email=None,
            guest_nom_complet=None,
            guest_phone=None,
            promo=promo if j % 4 == 0 else None,
            statut=TicketStatus.PAYE if j % 2 == 0 else TicketStatus.CREE,
            qr_code=qr,
        )
        if billet.statut == TicketStatus.PAYE:
            _create_payment(
                db,
                billet=billet,
                montant=Decimal(str(billet.prix)),
                moyen="CARD",
                statut=PaymentStatus.SUCCES,
                date_paiement=now - timedelta(days=2),
            )

    expires_at = now + timedelta(days=get_settings().refresh_token_expire_days)
    _create_refresh_token(db, user=admin, revoked=False, expires_at=expires_at)
    _create_refresh_token(db, user=admin, revoked=True, expires_at=expires_at)
    _create_refresh_token(db, user=organisateurs[0], revoked=False, expires_at=expires_at)
    _create_refresh_token(db, user=participants[0], revoked=False, expires_at=expires_at)

    promos = db.execute(select(PromoCode)).scalars().all()
    for promo in promos:
        promo.used_count = int(
            db.execute(select(func.count()).select_from(Billet).where(Billet.promo_code_id == promo.id)).scalar_one()
        )
        db.add(promo)
    db.flush()

    return SeedResult(
        countries=db.execute(select(func.count()).select_from(Country)).scalar_one(),
        administrative_levels=db.execute(select(func.count()).select_from(AdministrativeLevel)).scalar_one(),
        administrative_units=db.execute(select(func.count()).select_from(AdministrativeUnit)).scalar_one(),
        organisations=db.execute(select(func.count()).select_from(Organisation)).scalar_one(),
        utilisateurs=db.execute(select(func.count()).select_from(Utilisateur)).scalar_one(),
        evenements=db.execute(select(func.count()).select_from(Evenement)).scalar_one(),
        ticket_types=db.execute(select(func.count()).select_from(TicketType)).scalar_one(),
        promo_codes=db.execute(select(func.count()).select_from(PromoCode)).scalar_one(),
        billets=db.execute(select(func.count()).select_from(Billet)).scalar_one(),
        paiements=db.execute(select(func.count()).select_from(Paiement)).scalar_one(),
        scans=db.execute(select(func.count()).select_from(TicketScan)).scalar_one(),
        notifications=db.execute(select(func.count()).select_from(Notification)).scalar_one(),
        refresh_tokens=db.execute(select(func.count()).select_from(RefreshToken)).scalar_one(),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    with SessionLocal() as db:
        result = seed(db, reset=args.reset)
        db.commit()
    print(
        "Seed OK: "
        f"countries={result.countries}, administrative_levels={result.administrative_levels}, "
        f"administrative_units={result.administrative_units}, organisations={result.organisations}, "
        f"utilisateurs={result.utilisateurs}, evenements={result.evenements}, ticket_types={result.ticket_types}, "
        f"promo_codes={result.promo_codes}, billets={result.billets}, paiements={result.paiements}, "
        f"scans={result.scans}, notifications={result.notifications}, refresh_tokens={result.refresh_tokens}"
    )


if __name__ == "__main__":
    main()
