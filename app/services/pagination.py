from __future__ import annotations

from typing import TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

T = TypeVar("T")


def paginate(
    db: Session,
    stmt,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[T], int]:
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.limit(limit).offset(offset)).scalars().all()
    return items, int(total)

