from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    title: str
    body: str
    is_read: bool
    created_at: datetime


class NotificationMarkRead(BaseModel):
    is_read: bool = Field(default=True)

