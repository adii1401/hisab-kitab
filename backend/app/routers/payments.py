from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_db
from app.core.auth import require_role
from app.models import (
    Payment, PaymentDirection, PaymentMode, PaymentStatus,
    Trip, TripStatus, User, UserRole, AuditLog
)
import json

router = APIRouter()


class PaymentCreate(BaseModel):
    trip_id: UUID
    direction: PaymentDirection
    amount: Decimal = Field(..., gt=0)
    mode: PaymentMode
    payment_date: Optional[date] = None
    reference_no: Optional[str] = None
    bank_account_to: Optional[str] = None
    upi_id_to: Optional[str] = None
    notes: Optional[str] = None
    is_manual: bool = False


class PaymentApprove(BaseModel):
    rejection_reason: Optional[str] = None


class PaymentConfirm(BaseModel):
    bank_statement_ref: Optional[str] = None
    reference_no: Optional[str] = None
    payment_date: Optional[date] = None


def serialize_payment(p: Payment) -> dict:
    return {
        "id": str(p.id),
        "trip_id": str(p.trip_id),
        "direction": p.direction.value,
        "amount": str(p.amount),
        "mode": p.mode.value,
        "status": p.status.value,
        "payment_date": str(p.payment_date) if p.payment_date else None,
        "reference_no": p.reference_no,
        "bank_account_to": p.bank_account_to,
        "upi_id_to": p.upi_id_to,
        "bank_statement_ref": p.bank_statement_ref,
        "notes": p.notes,
        "rejection_reason": p.rejection_reason,
        "created_at": str(p.created_at),
        "approved_at": str(p.approved_at) if p.approved_at else None,
        "vendor_name": p.vendor.name if p.vendor else None,
        "mill_name": p.mill.name if p.mill else None,
    }


async def _maybe_settle_trip(trip: Trip, db: AsyncSession):
    if trip.status == TripStatus.settled:
        return
    confirmed_out = sum(
        p.amount for p in trip.payments
        if p.direction == PaymentDirection.outgoing
        and p.status in (PaymentStatus.confirmed, PaymentStatus.manual)
    )
    confirmed_in = sum(
        p.amount for p in trip.payments
        if p.direction == PaymentDirection.incoming
        and p.status in (PaymentStatus.confirmed, PaymentStatus.manual)
    )
    if confirmed_out >= trip.vendor_total_amount - Decimal("0.01") and \
       confirmed_in >= trip.mill_total_amount - Decimal("0.01"):
        trip.status = TripStatus.settled


@router.post("", status_code=201)
async def create_payment(
    body: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.data_entry)),
):
    if body.is_manual and current_user.role != UserRole.admin:
        raise HTTPException(403, "Only admins can create manual payment records")

    result = await db.execute(
        select(Trip)
        .options(selectinload(Trip.payments), selectinload(Trip.mill_receipt))
        .where(Trip.id == body.trip_id)
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(404, "Trip not found")
    if trip.status == TripStatus.pickup:
        raise HTTPException(400, "Enter mill receipt before recording payments")

    if body.direction == PaymentDirection.outgoing:
        if body.amount > trip.vendor_balance + Decimal("0.01"):
            raise HTTPException(400, f"Amount exceeds vendor balance {trip.vendor_balance}")
        vendor_id, mill_id = trip.vendor_id, None
    else:
        if body.amount > trip.mill_balance + Decimal("0.01"):
            raise HTTPException(400, f"Amount exceeds mill balance {trip.mill_balance}")
        vendor_id, mill_id = None, trip.mill_id

    payment = Payment(
        trip_id=body.trip_id,
        vendor_id=vendor_id,
        mill_id=mill_id,
        direction=body.direction,
        amount=body.amount,
        mode=body.mode,
        status=PaymentStatus.manual if body.is_manual else PaymentStatus.draft,
        payment_date=body.payment_date,
        reference_no=body.reference_no,
        bank_account_to=body.bank_account_to,
        upi_id_to=body.upi_id_to,
        notes=body.notes,
        created_by=current_user.id,
    )
    db.add(payment)
    await db.flush()

    if body.is_manual:
        trip.payments.append(payment)
        await _maybe_settle_trip(trip, db)

    db.add(AuditLog(user_id=current_user.id, action="payment.create",
                    entity_type="payment", entity_id=str(payment.id)))
    await db.commit()
    await db.refresh(payment)

    result = await db.execute(
        select(Payment)
        .options(selectinload(Payment.vendor), selectinload(Payment.mill))
        .where(Payment.id == payment.id)
    )
    return serialize_payment(result.scalar_one())


@router.post("/{payment_id}/submit")
async def submit_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.data_entry)),
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(404, "Payment not found")
    if payment.status != PaymentStatus.draft:
        raise HTTPException(400, f"Cannot submit payment in status '{payment.status}'")
    payment.status = PaymentStatus.pending_approval
    await db.commit()
    return {"status": "submitted"}


@router.post("/{payment_id}/approve")
async def approve_payment(
    payment_id: UUID,
    body: PaymentApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    result = await db.execute(
        select(Payment)
        .options(selectinload(Payment.trip).selectinload(Trip.payments)
                 .selectinload(Trip.mill_receipt))
        .where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(404, "Payment not found")
    if payment.status != PaymentStatus.pending_approval:
        raise HTTPException(400, "Payment is not pending approval")

    now = datetime.now(timezone.utc)
    if body.rejection_reason:
        payment.status = PaymentStatus.rejected
        payment.rejection_reason = body.rejection_reason
    else:
        payment.status = PaymentStatus.approved
        payment.approved_by = current_user.id
        payment.approved_at = now
        if payment.direction == PaymentDirection.incoming:
            payment.status = PaymentStatus.confirmed
            payment.verified_at = now
            await _maybe_settle_trip(payment.trip, db)

    await db.commit()
    return {"status": payment.status.value}


@router.post("/{payment_id}/execute")
async def mark_executed(
    payment_id: UUID,
    body: PaymentConfirm,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.data_entry)),
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(404, "Payment not found")
    if payment.status != PaymentStatus.approved:
        raise HTTPException(400, "Payment must be approved first")
    payment.status = PaymentStatus.executed
    if body.reference_no: payment.reference_no = body.reference_no
    if body.payment_date: payment.payment_date = body.payment_date
    await db.commit()
    return {"status": "executed"}


@router.post("/{payment_id}/confirm")
async def confirm_payment(
    payment_id: UUID,
    body: PaymentConfirm,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    result = await db.execute(
        select(Payment)
        .options(selectinload(Payment.trip).selectinload(Trip.payments)
                 .selectinload(Trip.mill_receipt))
        .where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(404, "Payment not found")
    if payment.status not in (PaymentStatus.executed, PaymentStatus.approved):
        raise HTTPException(400, f"Cannot confirm payment in status '{payment.status}'")
    payment.status = PaymentStatus.confirmed
    payment.verified_at = datetime.now(timezone.utc)
    if body.bank_statement_ref: payment.bank_statement_ref = body.bank_statement_ref
    if body.reference_no: payment.reference_no = body.reference_no
    if body.payment_date: payment.payment_date = body.payment_date
    await _maybe_settle_trip(payment.trip, db)
    await db.commit()
    return {"status": "confirmed"}


@router.get("")
async def list_payments(
    trip_id: Optional[UUID] = None,
    direction: Optional[PaymentDirection] = None,
    status: Optional[PaymentStatus] = None,
    pending_approval: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.view_only)),
):
    filters = []
    if trip_id: filters.append(Payment.trip_id == trip_id)
    if direction: filters.append(Payment.direction == direction)
    if status: filters.append(Payment.status == status)
    if pending_approval: filters.append(Payment.status == PaymentStatus.pending_approval)

    result = await db.execute(
        select(Payment)
        .options(selectinload(Payment.vendor), selectinload(Payment.mill))
        .where(and_(*filters) if filters else True)
        .order_by(Payment.created_at.desc())
        .limit(100)
    )
    return [serialize_payment(p) for p in result.scalars().all()]
