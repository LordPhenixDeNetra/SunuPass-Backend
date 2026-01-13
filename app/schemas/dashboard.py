from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel


class SalesTimePoint(BaseModel):
    period_start: str
    tickets_created: int
    payments_success: int
    revenue_success: Decimal


class TicketTypeDashboard(BaseModel):
    ticket_type_id: uuid.UUID | None
    code: str
    label: str | None
    quota: int | None
    tickets_total: int
    tickets_active: int
    tickets_paid: int
    tickets_used: int
    tickets_cancelled: int
    revenue_success: Decimal


class EventDashboard(BaseModel):
    evenement_id: uuid.UUID
    capacite: int
    tickets_active: int
    capacity_remaining: int
    capacity_usage_rate: Decimal
    tickets_total: int
    tickets_paid: int
    tickets_used: int
    tickets_cancelled: int
    tickets_guest: int
    participants_unique: int
    scans_total: int
    payments_pending: int
    payments_success: int
    payments_failed: int
    payments_refunded: int
    revenue_success: Decimal
    revenue_refunded: Decimal
    by_ticket_type: list[TicketTypeDashboard]
    sales_daily: list[SalesTimePoint]
    sales_weekly: list[SalesTimePoint]
    sales_monthly: list[SalesTimePoint]
