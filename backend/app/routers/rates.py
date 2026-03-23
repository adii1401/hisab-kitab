from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_db
from app.core.auth import require_role
from app.models import DailyRate, Vendor, Mill, User, UserRole

router = APIRouter()


class RateSet(BaseModel):
    rate_date: date
    party_id: UUID
    party_type: str  # "vendor" or "mill"
    rate_per_kg: Decimal


class RateOut(BaseModel):
    id: str
    rate_date: date
    party_id: str
    party_type: str
    party_name: str
    rate_per_kg: Decimal


class BulkRateSet(BaseModel):
    rate_date: date
    vendor_rates: List[dict] = []  # [{"party_id": uuid, "rate_per_kg": decimal}]
    mill_rates: List[dict] = []


@router.get("", response_model=List[RateOut])
async def get_rates(
    rate_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.view_only)),
):
    """Get all rates for a given date."""
    result = await db.execute(
        select(DailyRate).where(DailyRate.rate_date == rate_date)
    )
    rates = result.scalars().all()

    out = []
    for r in rates:
        name = "Unknown"
        if r.party_type == "vendor":
            vr = await db.execute(select(Vendor).where(Vendor.id == r.party_id))
            v = vr.scalar_one_or_none()
            name = v.name if v else "Unknown"
        else:
            mr = await db.execute(select(Mill).where(Mill.id == r.party_id))
            m = mr.scalar_one_or_none()
            name = m.name if m else "Unknown"

        out.append(RateOut(
            id=str(r.id), rate_date=r.rate_date,
            party_id=str(r.party_id), party_type=r.party_type,
            party_name=name, rate_per_kg=r.rate_per_kg,
        ))
    return out


@router.post("/bulk")
async def set_bulk_rates(
    body: BulkRateSet,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.data_entry)),
):
    """
    Set all rates for a given date at once.
    Replaces any existing rates for that date.
    """
    # Delete existing for this date
    await db.execute(
        delete(DailyRate).where(DailyRate.rate_date == body.rate_date)
    )

    for item in body.vendor_rates:
        rate = Decimal(str(item["rate_per_kg"]))
        if rate > 0:
            db.add(DailyRate(
                rate_date=body.rate_date,
                party_id=item["party_id"],
                party_type="vendor",
                rate_per_kg=rate,
                set_by=current_user.id,
            ))

    for item in body.mill_rates:
        rate = Decimal(str(item["rate_per_kg"]))
        if rate > 0:
            db.add(DailyRate(
                rate_date=body.rate_date,
                party_id=item["party_id"],
                party_type="mill",
                rate_per_kg=rate,
                set_by=current_user.id,
            ))

    await db.commit()
    return {"status": "saved", "date": str(body.rate_date)}


@router.post("/single")
async def set_single_rate(
    body: RateSet,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.data_entry)),
):
    """Upsert a single rate entry."""
    existing = await db.execute(
        select(DailyRate).where(
            and_(
                DailyRate.rate_date == body.rate_date,
                DailyRate.party_id == body.party_id,
                DailyRate.party_type == body.party_type,
            )
        )
    )
    rate = existing.scalar_one_or_none()
    if rate:
        rate.rate_per_kg = body.rate_per_kg
        rate.set_by = current_user.id
    else:
        rate = DailyRate(
            rate_date=body.rate_date,
            party_id=body.party_id,
            party_type=body.party_type,
            rate_per_kg=body.rate_per_kg,
            set_by=current_user.id,
        )
        db.add(rate)
    await db.commit()
    return {"status": "saved"}