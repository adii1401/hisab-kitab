from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_db
from app.core.auth import require_role
from app.models import Trip, TripStatus, PaymentDirection, PaymentStatus, User, UserRole

router = APIRouter()

class LedgerRow(BaseModel):
    invoice_no: Optional[str] # Changed from trip_id to prioritize Invoice No
    date: date
    vehicle_no: str
    quantity_kg: Decimal # Renamed for accounting clarity
    rate: Decimal # Added to show the negotiated rate
    invoice_amount: Decimal
    paid_amount: Decimal
    balance: Decimal
    status: str

class LedgerSummary(BaseModel):
    party_id: str
    party_name: str
    party_type: str
    total_invoice: Decimal
    total_paid: Decimal
    total_balance: Decimal
    total_margin: Optional[Decimal]
    count: int
    rows: List[LedgerRow]

@router.get("/summary")
async def get_ledger(
    party_type: str = Query(..., description="vendor or mill"),
    party_id: UUID = Query(...),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.view_only)),
):
    filters = []
    if party_type == "vendor":
        filters.append(Trip.vendor_id == party_id)
    else:
        filters.append(Trip.mill_id == party_id)
    
    if date_from: filters.append(Trip.trip_date >= date_from)
    if date_to: filters.append(Trip.trip_date <= date_to)

    result = await db.execute(
        select(Trip)
        .options(
            selectinload(Trip.vendor),
            selectinload(Trip.mill),
            selectinload(Trip.payments),
        )
        .where(and_(*filters))
        .order_by(Trip.trip_date.desc())
    )
    trips = result.scalars().all()

    rows = []
    total_invoice = Decimal("0")
    total_paid = Decimal("0")
    total_margin = Decimal("0")

    for trip in trips:
        if party_type == "vendor":
            invoice = trip.vendor_total_amount
            rate = trip.vendor_rate_per_kg
            paid = sum(
                p.amount for p in trip.payments
                if p.direction == PaymentDirection.outgoing
                and p.status in (PaymentStatus.confirmed, PaymentStatus.manual)
            )
        else:
            invoice = trip.mill_total_amount
            rate = trip.mill_default_rate_per_kg
            paid = sum(
                p.amount for p in trip.payments
                if p.direction == PaymentDirection.incoming
                and p.status in (PaymentStatus.confirmed, PaymentStatus.manual)
            )

        balance = invoice - paid
        total_invoice += invoice
        total_paid += paid
        total_margin += (trip.our_margin or 0)

        rows.append(LedgerRow(
            invoice_no=trip.eway_bill_no, # Maps to the Manual Invoice No entered
            date=trip.trip_date,
            vehicle_no=trip.vehicle_no,
            quantity_kg=trip.loaded_weight_kg, # This is the Net Weight entered
            rate=rate,
            invoice_amount=invoice,
            paid_amount=paid,
            balance=max(Decimal("0"), balance),
            status=trip.status.value,
        ))

    party_name = "Unknown"
    if trips:
        party_name = trips[0].vendor.name if party_type == "vendor" else trips[0].mill.name

    return LedgerSummary(
        party_id=str(party_id),
        party_name=party_name,
        party_type=party_type,
        total_invoice=total_invoice,
        total_paid=total_paid,
        total_balance=max(Decimal("0"), total_invoice - total_paid),
        total_margin=total_margin if party_type == "vendor" else None,
        count=len(trips),
        rows=rows,
    )

@router.get("/pending")
async def pending_balances(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.view_only)),
):
    """Dashboard: Summary of all outstanding market-grade balances."""
    result = await db.execute(
        select(Trip)
        .options(
            selectinload(Trip.vendor),
            selectinload(Trip.mill),
            selectinload(Trip.payments),
        )
        .where(Trip.status != TripStatus.settled)
        .order_by(Trip.trip_date.desc())
        .limit(100)
    )
    trips = result.scalars().all()

    total_vendor_due = Decimal("0")
    total_mill_due = Decimal("0")
    items = []

    for t in trips:
        vb = t.vendor_balance
        mb = t.mill_balance
        total_vendor_due += vb
        total_mill_due += mb
        
        items.append({
            "invoice_no": t.eway_bill_no,
            "date": str(t.trip_date),
            "vendor": t.vendor.name,
            "mill": t.mill.name,
            "vehicle": t.vehicle_no,
            "vendor_due": str(vb),
            "mill_due": str(mb),
            "margin": str(t.our_margin)
        })

    return {
        "total_vendor_due": str(total_vendor_due),
        "total_mill_due": str(total_mill_due),
        "invoices": items,
    }