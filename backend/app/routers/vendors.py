from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_db
from app.core.auth import require_role
from app.models import Vendor, User, UserRole

router = APIRouter()


class VendorCreate(BaseModel):
    name: str
    gstin: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None
    upi_id: Optional[str] = None
    notes: Optional[str] = None


class VendorUpdate(VendorCreate):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class VendorOut(BaseModel):
    id: str
    name: str
    gstin: Optional[str]
    phone: Optional[str]
    city: Optional[str]
    address: Optional[str]
    bank_name: Optional[str]
    bank_account: Optional[str]
    bank_ifsc: Optional[str]
    upi_id: Optional[str]
    is_active: bool
    notes: Optional[str]

    class Config:
        from_attributes = True


def to_out(v: Vendor) -> VendorOut:
    return VendorOut(
        id=str(v.id), name=v.name, gstin=v.gstin, phone=v.phone,
        city=v.city, address=v.address, bank_name=v.bank_name,
        bank_account=v.bank_account, bank_ifsc=v.bank_ifsc,
        upi_id=v.upi_id, is_active=v.is_active, notes=v.notes,
    )


@router.get("", response_model=List[VendorOut])
async def list_vendors(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.view_only)),
):
    q = select(Vendor).order_by(Vendor.name)
    if active_only:
        q = q.where(Vendor.is_active == True)
    result = await db.execute(q)
    return [to_out(v) for v in result.scalars().all()]


@router.post("", response_model=VendorOut, status_code=201)
async def create_vendor(
    body: VendorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.data_entry)),
):
    vendor = Vendor(**body.model_dump())
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return to_out(vendor)


@router.get("/{vendor_id}", response_model=VendorOut)
async def get_vendor(
    vendor_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.view_only)),
):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(404, "Vendor not found")
    return to_out(vendor)


@router.patch("/{vendor_id}", response_model=VendorOut)
async def update_vendor(
    vendor_id: UUID,
    body: VendorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.data_entry)),
):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(404, "Vendor not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(vendor, field, value)
    await db.commit()
    return to_out(vendor)