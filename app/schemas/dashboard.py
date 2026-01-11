from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel


class EventDashboard(BaseModel):
    evenement_id: uuid.UUID
    tickets_total: int
    tickets_paid: int
    tickets_used: int
    tickets_cancelled: int
    payments_pending: int
    revenue_success: Decimal
    revenue_refunded: Decimal

