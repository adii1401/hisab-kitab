import csv
import io
from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_db
from app.core.auth import require_role
from app.models import Trip, TripStatus, PaymentDirection, PaymentStatus, User, UserRole

router = APIRouter()

class LedgerRow(BaseModel):
    invoice_no: Optional[str] 
    date: date
    vehicle_no: str
    quantity_kg: Decimal 
    rate: Decimal 
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

@router.get("/summary", response_model=LedgerSummary)
async def get_ledger(
    party_type: str = Query(..., description="vendor or mill"),
    party_id: UUID = Query(...),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    # Temporarily removed role check for easy testing. Add back for production.
    # current_user: User = Depends(require_role(UserRole.view_only)),
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
        .order_by(Trip.trip_date.asc()) # Changed to ASC for proper running balance calculation
    )
    trips = result.scalars().all()

    rows = []
    total_invoice = Decimal("0")
    total_paid = Decimal("0")
    total_margin = Decimal("0")
    running_balance = Decimal("0")

    for trip in trips:
        if party_type == "vendor":
            invoice = trip.vendor_total_amount or Decimal("0")
            rate = trip.vendor_rate_per_kg
            paid = sum(
                p.amount for p in trip.payments
                if p.direction == PaymentDirection.outgoing
                and p.status in (PaymentStatus.confirmed, PaymentStatus.manual)
            )
        else:
            invoice = trip.mill_total_amount or Decimal("0")
            rate = trip.mill_default_rate_per_kg
            paid = sum(
                p.amount for p in trip.payments
                if p.direction == PaymentDirection.incoming
                and p.status in (PaymentStatus.confirmed, PaymentStatus.manual)
            )

        # Market-grade running balance logic
        running_balance += (invoice - paid)
        
        total_invoice += invoice
        total_paid += paid
        total_margin += (trip.our_margin or Decimal("0"))

        rows.append(LedgerRow(
            invoice_no=trip.eway_bill_no,
            date=trip.trip_date,
            vehicle_no=trip.vehicle_no,
            quantity_kg=trip.loaded_weight_kg,
            rate=rate,
            invoice_amount=invoice,
            paid_amount=paid,
            balance=max(Decimal("0"), running_balance),
            status=trip.status.value,
        ))

    # Reverse the rows for display (newest first on top), but balance was calculated chronologically
    rows.reverse()

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

# --- NEW: CSV EXPORT ENDPOINT ---
@router.get("/export")
async def export_ledger_csv(
    party_type: str = Query(..., description="vendor or mill"),
    party_id: UUID = Query(...),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    # Fetch the ledger data using the existing function
    summary = await get_ledger(party_type, party_id, date_from, date_to, db)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 1. Header Information
    writer.writerow(["GUPTA TRADING COMPANY - LEDGER REPORT"])
    writer.writerow(["Party Type:", summary.party_type.capitalize()])
    writer.writerow(["Party Name:", summary.party_name])
    writer.writerow(["Date Range:", f"{date_from or 'All Time'} to {date_to or 'Present'}"])
    writer.writerow([])
    
    # 2. Table Headers
    writer.writerow(["Date", "Invoice / E-Way No", "Vehicle", "Net Wt (Kg)", "Rate", "Bill Amount", "Paid Amount", "Balance"])
    
    # 3. Data Rows (Re-reversed to show chronological order in Excel)
    chronological_rows = reversed(summary.rows)
    for row in chronological_rows:
        writer.writerow([
            row.date, 
            row.invoice_no, 
            row.vehicle_no, 
            float(row.quantity_kg), 
            float(row.rate), 
            float(row.invoice_amount), 
            float(row.paid_amount), 
            float(row.balance)
        ])
    
    # 4. Summary Footer
    writer.writerow([])
    writer.writerow(["", "", "", "", "TOTALS:", float(summary.total_invoice), float(summary.total_paid), float(summary.total_balance)])

    output.seek(0)
    
    filename = f"{summary.party_name}_Ledger.csv".replace(" ", "_")
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv", 
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/pending")
async def pending_balances(
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(require_role(UserRole.view_only)),
):
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
        # Vendor Balance (Uses the property method)
        vb = t.vendor_balance
        
        # Mill Balance (Manual calculation because we changed it to a column)
        mill_paid = sum(
            p.amount for p in t.payments
            if p.direction == PaymentDirection.incoming
            and p.status in (PaymentStatus.confirmed, PaymentStatus.manual)
        )
        mb = max(Decimal("0"), (t.mill_total_amount or Decimal("0")) - mill_paid)
        
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
            "margin": str(t.our_margin or "0.00")
        })

    return {
        "total_vendor_due": str(total_vendor_due),
        "total_mill_due": str(total_mill_due),
        "invoices": items,
    }