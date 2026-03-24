import enum
import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime, Enum,
    ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    admin      = "admin"
    data_entry = "data_entry"
    view_only  = "view_only"

class TripStatus(str, enum.Enum):
    pickup   = "pickup"
    received = "received"
    delivered = "delivered" 
    settled  = "settled"

class PaymentMode(str, enum.Enum):
    cash   = "cash"
    upi    = "upi"
    neft   = "neft"
    rtgs   = "rtgs"
    cheque = "cheque"

class PaymentDirection(str, enum.Enum):
    outgoing = "outgoing"
    incoming = "incoming"

class PaymentStatus(str, enum.Enum):
    draft            = "draft"
    pending_approval = "pending_approval"
    approved         = "approved"
    executed         = "executed"
    confirmed        = "confirmed"
    rejected         = "rejected"
    manual           = "manual"

class MaterialType(str, enum.Enum):
    kartoon   = "Kartoon / corrugated box"
    greyboard = "Grey board"
    newspaper = "Old newspaper"
    books     = "Old books / magazines"
    white     = "White paper"
    duplex    = "Duplex board"
    other     = "Other"


class User(Base):
    __tablename__ = "users"
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email            = Column(String(255), unique=True, nullable=False, index=True)
    full_name        = Column(String(255), nullable=False)
    hashed_password  = Column(String(255), nullable=False)
    role             = Column(Enum(UserRole), nullable=False, default=UserRole.view_only)
    is_active        = Column(Boolean, default=True, nullable=False)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at    = Column(DateTime(timezone=True), nullable=True)
    trips_created    = relationship("Trip", back_populates="created_by_user", foreign_keys="Trip.created_by")
    payments_created = relationship("Payment", back_populates="created_by_user", foreign_keys="Payment.created_by")
    payments_approved = relationship("Payment", back_populates="approved_by_user", foreign_keys="Payment.approved_by")


class Vendor(Base):
    __tablename__ = "vendors"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name         = Column(String(255), nullable=False, index=True)
    gstin        = Column(String(15), nullable=True)
    phone        = Column(String(20), nullable=True)
    city         = Column(String(100), nullable=True)
    address      = Column(Text, nullable=True)
    bank_name    = Column(String(100), nullable=True)
    bank_account = Column(String(30), nullable=True)
    bank_ifsc    = Column(String(15), nullable=True)
    upi_id       = Column(String(100), nullable=True)
    is_active    = Column(Boolean, default=True)
    notes        = Column(Text, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    trips        = relationship("Trip", back_populates="vendor")
    payments     = relationship("Payment", back_populates="vendor")


class Mill(Base):
    __tablename__ = "mills"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name         = Column(String(255), nullable=False, index=True)
    gstin        = Column(String(15), nullable=True)
    phone        = Column(String(20), nullable=True)
    city         = Column(String(100), nullable=True)
    address      = Column(Text, nullable=True)
    bank_name    = Column(String(100), nullable=True)
    bank_account = Column(String(30), nullable=True)
    bank_ifsc    = Column(String(15), nullable=True)
    upi_id       = Column(String(100), nullable=True)
    credit_days  = Column(Integer, default=30, nullable=True)
    is_active    = Column(Boolean, default=True)
    notes        = Column(Text, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    trips        = relationship("Trip", back_populates="mill")
    payments     = relationship("Payment", back_populates="mill")


class DailyRate(Base):
    __tablename__ = "daily_rates"
    __table_args__ = (
        UniqueConstraint("rate_date", "party_id", "party_type", name="uq_daily_rate"),
    )
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rate_date    = Column(Date, nullable=False, index=True)
    party_id     = Column(UUID(as_uuid=True), nullable=False)
    party_type   = Column(String(10), nullable=False)
    rate_per_kg  = Column(Numeric(10, 4), nullable=False)
    set_by       = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())


class Trip(Base):
    __tablename__ = "trips"
    id                       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_date                = Column(Date, nullable=False, index=True)
    vendor_id                = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False, index=True)
    mill_id                  = Column(UUID(as_uuid=True), ForeignKey("mills.id"), nullable=False, index=True)
    vehicle_no               = Column(String(20), nullable=False)
    driver_name              = Column(String(100), nullable=True)
    driver_phone             = Column(String(20), nullable=True)
    tare_weight_kg           = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    loaded_weight_kg         = Column(Numeric(12, 2), nullable=False)
    vendor_rate_per_kg       = Column(Numeric(10, 4), nullable=False)
    mill_default_rate_per_kg = Column(Numeric(10, 4), nullable=False)
    hsn_code                 = Column(String(10), nullable=False, default="47079000")
    gst_percent              = Column(Numeric(5, 2), nullable=False, default=Decimal("5.00"))
    advance_paid_to_vendor   = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    freight_cost             = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    eway_bill_no             = Column(String(20), nullable=True)
    
    # --- E-WAY BILL & LOGISTICS TRACKING FIELDS ---
    transaction_type         = Column(String(50), nullable=False, default="regular")
    dispatch_pincode         = Column(String(10), nullable=True)
    ship_to_pincode          = Column(String(10), nullable=True)

    # --- FINANCIAL COLUMNS (Replaced Properties) ---
    mill_base_amount         = Column(Numeric(14, 2), nullable=True)
    mill_gst_amount          = Column(Numeric(14, 2), nullable=True)
    mill_total_amount        = Column(Numeric(14, 2), nullable=True)
    vendor_total_amount      = Column(Numeric(14, 2), nullable=True)
    our_margin               = Column(Numeric(14, 2), nullable=True)

    status                   = Column(Enum(TripStatus), nullable=False, default=TripStatus.pickup, index=True)
    notes                    = Column(Text, nullable=True)
    created_by               = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at               = Column(DateTime(timezone=True), server_default=func.now())
    updated_at               = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    vendor          = relationship("Vendor", back_populates="trips")
    mill            = relationship("Mill", back_populates="trips")
    created_by_user = relationship("User", back_populates="trips_created", foreign_keys=[created_by])
    mill_receipt    = relationship("MillReceipt", back_populates="trip", uselist=False)
    payments        = relationship("Payment", back_populates="trip")
    invoice         = relationship("Invoice", back_populates="trip", uselist=False)

    # Note: vendor_balance remains a property because it's calculated dynamically based on related Payments
    @property
    def vendor_balance(self):
        paid = sum(p.amount for p in self.payments
                   if p.direction == PaymentDirection.outgoing and p.status == PaymentStatus.confirmed)
        return max(Decimal("0"), (self.vendor_total_amount or Decimal("0")) - paid)


class MillReceipt(Base):
    __tablename__ = "mill_receipts"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id      = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False, unique=True, index=True)
    slip_no      = Column(String(50), nullable=True)
    receipt_date = Column(Date, nullable=True)
    moisture_pct = Column(Numeric(6, 3), nullable=True)
    notes        = Column(Text, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    trip  = relationship("Trip", back_populates="mill_receipt")
    lines = relationship("MillReceiptLine", back_populates="receipt", cascade="all, delete-orphan")

    @property
    def net_weight_kg(self):
        return sum(l.qty_kg for l in self.lines)


class MillReceiptLine(Base):
    __tablename__ = "mill_receipt_lines"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id    = Column(UUID(as_uuid=True), ForeignKey("mill_receipts.id"), nullable=False, index=True)
    material_type = Column(Enum(MaterialType), nullable=False)
    qty_kg        = Column(Numeric(12, 2), nullable=False)
    rate_per_kg   = Column(Numeric(10, 4), nullable=False)
    receipt = relationship("MillReceipt", back_populates="lines")


class Payment(Base):
    __tablename__ = "payments"
    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id            = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False, index=True)
    vendor_id          = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=True)
    mill_id            = Column(UUID(as_uuid=True), ForeignKey("mills.id"), nullable=True)
    direction          = Column(Enum(PaymentDirection), nullable=False)
    amount             = Column(Numeric(14, 2), nullable=False)
    mode               = Column(Enum(PaymentMode), nullable=False)
    status             = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.draft, index=True)
    reference_no       = Column(String(100), nullable=True)
    bank_account_to    = Column(String(30), nullable=True)
    upi_id_to          = Column(String(100), nullable=True)
    payment_date       = Column(Date, nullable=True)
    notes              = Column(Text, nullable=True)
    bank_statement_ref = Column(String(100), nullable=True)
    verified_at        = Column(DateTime(timezone=True), nullable=True)
    created_by         = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_by        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at        = Column(DateTime(timezone=True), nullable=True)
    rejection_reason   = Column(Text, nullable=True)
    created_at         = Column(DateTime(timezone=True), server_default=func.now())
    updated_at         = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    trip             = relationship("Trip", back_populates="payments")
    vendor           = relationship("Vendor", back_populates="payments")
    mill             = relationship("Mill", back_populates="payments")
    created_by_user  = relationship("User", back_populates="payments_created", foreign_keys=[created_by])
    approved_by_user = relationship("User", back_populates="payments_approved", foreign_keys=[approved_by])


class Invoice(Base):
    __tablename__ = "invoices"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id      = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False, unique=True, index=True)
    invoice_no   = Column(String(30), unique=True, nullable=False)
    invoice_date = Column(Date, nullable=False)
    irn          = Column(String(100), nullable=True)
    ack_no       = Column(String(50), nullable=True) 
    pdf_path     = Column(String(500), nullable=True)
    created_by   = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    
    trip = relationship("Trip", back_populates="invoice")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id     = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action      = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id   = Column(String(36), nullable=True)
    detail      = Column(Text, nullable=True)
    ip_address  = Column(String(45), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), index=True)