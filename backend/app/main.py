from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
# 1. FIXED: We import the limiter from core.auth to prevent Circular Imports
from app.core.auth import limiter 
from app.routers import auth, users, vendors, mills, rates, invoices, receipts, payments, ledger, reports

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.PDF_STORAGE_PATH, exist_ok=True)
    yield

# 2. MARKET-GRADE SECURITY: Hide Swagger API Docs if we are not in development mode
is_dev = settings.ENVIRONMENT == "development"

app = FastAPI(
    title="Hisab Kitab API",
    version="1.0.0",
    root_path="/api", 
    openapi_url="/openapi.json" if is_dev else None, # Hidden in Production
    docs_url="/docs" if is_dev else None,            # Hidden in Production
    redoc_url=None,
    lifespan=lifespan,
)

# Register the Rate Limiter to the FastAPI app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# SECURE CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081", 
        "http://localhost:5173",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:5173"
        # Note: If your father uses a specific Serveo URL (like https://gupta.serveo.net), add it here!
    ],
    allow_credentials=True, # CRITICAL: This allows HttpOnly secure cookies to pass
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "" 

app.include_router(auth.router,     prefix=PREFIX + "/auth",     tags=["Auth"])
app.include_router(users.router,    prefix=PREFIX + "/users",    tags=["Users"])
app.include_router(vendors.router,  prefix=PREFIX + "/vendors",  tags=["Vendors"])
app.include_router(mills.router,    prefix=PREFIX + "/mills",    tags=["Mills"])
app.include_router(rates.router,    prefix=PREFIX + "/rates",    tags=["Daily Rates"])
app.include_router(invoices.router, prefix=PREFIX + "/invoices", tags=["Invoices"])
app.include_router(receipts.router, prefix=PREFIX + "/receipts", tags=["Mill Receipts"])
app.include_router(payments.router, prefix=PREFIX + "/payments", tags=["Payments"])
app.include_router(ledger.router,   prefix=PREFIX + "/ledger",   tags=["Ledger"])
app.include_router(reports.router,  prefix=PREFIX + "/reports",  tags=["Reports"])

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}