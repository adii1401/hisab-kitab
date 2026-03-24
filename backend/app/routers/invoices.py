from datetime import date
from decimal import Decimal
from typing import Optional, Literal
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import get_db
from app.models import Trip, TripStatus

# Set up logging so you can see errors in PowerShell
logger = logging.getLogger(__name__)
router = APIRouter()

GST_SLABS = [Decimal("0"), Decimal("5.00"), Decimal("12.00"), Decimal("18.00"), Decimal("28.00")]

class InvoiceCreate(BaseModel):
    invoice_no: str
    invoice_date: date
    vendor_id: UUID
    mill_id: UUID
    vehicle_no: str
    driver_phone: Optional[str] = None
    hsn_code: str = "47079000"
    net_weight_kg: Decimal = Field(..., gt=0)
    negotiated_buy_rate: Decimal = Field(..., gt=0)
    negotiated_sell_rate: Decimal = Field(..., gt=0)
    gst_percent: Decimal = Decimal("5.00")
    advance_to_vendor: Decimal = Decimal("0")
    
    transaction_type: Literal['regular', 'bill_to_ship_to', 'bill_from_dispatch_from', 'combination'] = 'regular'
    dispatch_pincode: Optional[str] = None
    ship_to_pincode: Optional[str] = None

@router.get("")
async def get_invoices(limit: int = 100, db: AsyncSession = Depends(get_db)):
    query = select(Trip).order_by(Trip.trip_date.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/process-invoice")
async def process_invoice(body: InvoiceCreate, db: AsyncSession = Depends(get_db)):
    try:
        # 1. Validate GST Slab
        if body.gst_percent not in GST_SLABS:
            raise HTTPException(status_code=400, detail=f"Invalid GST Slab: {body.gst_percent}")

        # 2. Check for Duplicate Invoice No (eway_bill_no in Trip model)
        existing_check = await db.execute(select(Trip).where(Trip.eway_bill_no == body.invoice_no))
        if existing_check.scalars().first():
            raise HTTPException(status_code=400, detail=f"Invoice/E-Way Bill {body.invoice_no} already exists.")

        # 3. Zoho Style Calculations
        taxable = body.net_weight_kg * body.negotiated_sell_rate
        gst_amt = (taxable * body.gst_percent) / 100
        total_bill = taxable + gst_amt

        # 4. Create Trip record
        new_invoice = Trip(
            trip_date=body.invoice_date,
            vendor_id=body.vendor_id,
            mill_id=body.mill_id,
            vehicle_no=body.vehicle_no.upper(),
            driver_name=body.driver_phone, # Mapping phone to driver_name field
            eway_bill_no=body.invoice_no,
            loaded_weight_kg=body.net_weight_kg,
            vendor_rate_per_kg=body.negotiated_buy_rate,
            mill_default_rate_per_kg=body.negotiated_sell_rate,
            hsn_code=body.hsn_code,
            gst_percent=body.gst_percent,
            mill_total_amount=total_bill,
            status=TripStatus.delivered,
            transaction_type=body.transaction_type,
            dispatch_pincode=body.dispatch_pincode,
            ship_to_pincode=body.ship_to_pincode
        )

        db.add(new_invoice)
        await db.commit()
        await db.refresh(new_invoice)

        return {"status": "success", "invoice": body.invoice_no, "total": float(total_bill)}

    except Exception as e:
        # This will print the EXACT error in your PowerShell window
        logger.error(f"FATAL ERROR while creating invoice: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Backend Error: {str(e)}")