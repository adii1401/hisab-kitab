from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
# 1. FIX: Correct the import to match your project structure
from app.routers import auth, users, vendors, mills, rates, invoices, receipts, payments, ledger, reports

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.PDF_STORAGE_PATH, exist_ok=True)
    yield

app = FastAPI(
    title="Hisab Kitab API",
    version="1.0.0",
    root_path="/api", 
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Keep this EMPTY. root_path handles /api for you.
PREFIX = "" 

app.include_router(auth.router,     prefix=PREFIX + "/auth",     tags=["Auth"])
app.include_router(users.router,    prefix=PREFIX + "/users",    tags=["Users"])
app.include_router(vendors.router,  prefix=PREFIX + "/vendors",  tags=["Vendors"])
app.include_router(mills.router,    prefix=PREFIX + "/mills",    tags=["Mills"])
app.include_router(rates.router,    prefix=PREFIX + "/rates",    tags=["Daily Rates"])

# 3. FIX: Change tag and prefix to 'Invoices' to match your new logic
app.include_router(invoices.router, prefix=PREFIX + "/invoices", tags=["Invoices"])

app.include_router(receipts.router, prefix=PREFIX + "/receipts", tags=["Mill Receipts"])
app.include_router(payments.router, prefix=PREFIX + "/payments", tags=["Payments"])
app.include_router(ledger.router,   prefix=PREFIX + "/ledger",   tags=["Ledger"])
app.include_router(reports.router,  prefix=PREFIX + "/reports",  tags=["Reports"])

# 4. FIX: Remove /api from the route. root_path handles it!
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}