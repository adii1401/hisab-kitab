from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_db
from app.core.auth import require_role
from app.models import Mill, User, UserRole

router = APIRouter()


class MillCreate(BaseModel):
    name: str
    gstin: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None
    upi_id: Optional[str] = None
    credit_days: Optional[int] = 30
    notes: Optional[str] = None


class MillUpdate(MillCreate):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class MillOut(BaseModel):
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
    credit_days: Optional[int]
    is_active: bool
    notes: Optional[str]

    class Config:
        from_attributes = True


def to_out(m: Mill) -> MillOut:
    return MillOut(
        id=str(m.id), name=m.name, gstin=m.gstin, phone=m.phone,
        city=m.city, address=m.address, bank_name=m.bank_name,
        bank_account=m.bank_account, bank_ifsc=m.bank_ifsc,
        upi_id=m.upi_id, credit_days=m.credit_days,
        is_active=m.is_active, notes=m.notes,
    )


@router.get("", response_model=List[MillOut])
async def list_mills(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.view_only)),
):
    q = select(Mill).order_by(Mill.name)
    if active_only:
        q = q.where(Mill.is_active == True)
    result = await db.execute(q)
    return [to_out(m) for m in result.scalars().all()]


@router.post("", response_model=MillOut, status_code=201)
async def create_mill(
    body: MillCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.data_entry)),
):
    mill = Mill(**body.model_dump())
    db.add(mill)
    await db.commit()
    await db.refresh(mill)
    return to_out(mill)


@router.get("/{mill_id}", response_model=MillOut)
async def get_mill(
    mill_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.view_only)),
):
    result = await db.execute(select(Mill).where(Mill.id == mill_id))
    mill = result.scalar_one_or_none()
    if not mill:
        raise HTTPException(404, "Mill not found")
    return to_out(mill)


@router.patch("/{mill_id}", response_model=MillOut)
async def update_mill(
    mill_id: UUID,
    body: MillUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.data_entry)),
):
    result = await db.execute(select(Mill).where(Mill.id == mill_id))
    mill = result.scalar_one_or_none()
    if not mill:
        raise HTTPException(404, "Mill not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(mill, field, value)
    await db.commit()
    return to_out(mill)