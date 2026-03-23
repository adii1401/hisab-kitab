from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_db
from app.core.auth import require_role
from app.models import (
    MillReceipt, MillReceiptLine, MaterialType,
    Trip, TripStatus, User, UserRole, AuditLog
)

router = APIRouter()


class ReceiptLineIn(BaseModel):
    material_type: MaterialType
    qty_kg: Decimal
    rate_per_kg: Decimal


class ReceiptCreate(BaseModel):
    trip_id: UUID
    slip_no: Optional[str] = None
    receipt_date: Optional[date] = None
    moisture_pct: Optional[Decimal] = None
    notes: Optional[str] = None
    lines: List[ReceiptLineIn]


class ReceiptLineOut(BaseModel):
    id: str
    material_type: str
    qty_kg: Decimal
    rate_per_kg: Decimal
    amount: Decimal


class ReceiptOut(BaseModel):
    id: str
    trip_id: str
    slip_no: Optional[str]
    receipt_date: Optional[date]
    moisture_pct: Optional[Decimal]
    net_weight_kg: Decimal
    base_amount: Decimal
    notes: Optional[str]
    lines: List[ReceiptLineOut]


def serialize_receipt(r: MillReceipt) -> ReceiptOut:
    return ReceiptOut(
        id=str(r.id),
        trip_id=str(r.trip_id),
        slip_no=r.slip_no,
        receipt_date=r.receipt_date,
        moisture_pct=r.moisture_pct,
        net_weight_kg=r.net_weight_kg,
        base_amount=r.base_amount,
        notes=r.notes,
        lines=[
            ReceiptLineOut(
                id=str(l.id),
                material_type=l.material_type.value,
                qty_kg=l.qty_kg,
                rate_per_kg=l.rate_per_kg,
                amount=l.qty_kg * l.rate_per_kg,
            )
            for l in r.lines
        ],
    )


@router.post("", response_model=ReceiptOut, status_code=201)
async def create_receipt(
    body: ReceiptCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.data_entry)),
):
    # Load trip
    result = await db.execute(
        select(Trip)
        .options(selectinload(Trip.payments))
        .where(Trip.id == body.trip_id)
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(404, "Trip not found")
    if trip.status != TripStatus.pickup:
        raise HTTPException(400, "Receipt already entered for this trip")
    if not body.lines or all(l.qty_kg <= 0 for l in body.lines):
        raise HTTPException(400, "At least one material line with qty > 0 is required")

    receipt = MillReceipt(
        trip_id=body.trip_id,
        slip_no=body.slip_no,
        receipt_date=body.receipt_date,
        moisture_pct=body.moisture_pct,
        notes=body.notes,
    )
    db.add(receipt)
    await db.flush()

    for line in body.lines:
        if line.qty_kg > 0:
            db.add(MillReceiptLine(
                receipt_id=receipt.id,
                material_type=line.material_type,
                qty_kg=line.qty_kg,
                rate_per_kg=line.rate_per_kg,
            ))

    trip.status = TripStatus.received
    db.add(AuditLog(
        user_id=current_user.id,
        action="receipt.create",
        entity_type="trip",
        entity_id=str(trip.id),
    ))

    await db.commit()

    result = await db.execute(
        select(MillReceipt)
        .options(selectinload(MillReceipt.lines))
        .where(MillReceipt.id == receipt.id)
    )
    return serialize_receipt(result.scalar_one())


@router.get("/{trip_id}", response_model=ReceiptOut)
async def get_receipt(
    trip_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.view_only)),
):
    result = await db.execute(
        select(MillReceipt)
        .options(selectinload(MillReceipt.lines))
        .where(MillReceipt.trip_id == trip_id)
    )
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(404, "Receipt not found for this trip")
    return serialize_receipt(receipt)