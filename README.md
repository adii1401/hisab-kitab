# Hisab Kitab — Trading Management System

A full-stack trading, logistics, and accounting system built for the scrap paper and waste material industry. Handles truck dispatch, mill weighment, GST invoicing, and multi-party payment tracking.

---

## Features

- **Trip management** — Tare/loaded weight tracking, load calculation, e-way bill logging
- **Mill receipt entry** — Per-material-type weighment with moisture and penalty deductions
- **GST invoicing** — Auto-calculates CGST/SGST, generates print-ready PDF invoices
- **Vendor receipts** — Net weight × vendor rate − advance = balance due, sent as PDF
- **Payment workflow** — Human-in-loop: draft → submit → admin approve → execute → confirm
- **Daily rates** — Per-vendor buy rate and per-mill sell rate, set every morning
- **Ledger** — Real-time per-party statement with date range filter
- **Role-based access** — Admin, data entry, view-only
- **Audit log** — Every action recorded with user and timestamp

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, React Router |
| Backend | FastAPI, SQLAlchemy (async), Pydantic |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| PDF generation | ReportLab |
| Excel export | openpyxl |
| Infrastructure | Docker, Docker Compose, Nginx |

---

## Architecture

```
Browser
  └── Nginx (port 8080)
        ├── /api/*  → FastAPI backend (port 8000)
        └── /*      → React frontend (port 3000)

FastAPI
  ├── PostgreSQL  (all financial data)
  └── Redis       (session cache)
```

---

## Project Structure

```
hisab/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, all routers
│   │   ├── models.py            # SQLAlchemy models (10 tables)
│   │   ├── core/
│   │   │   ├── config.py        # Settings, DB session
│   │   │   ├── auth.py          # JWT + RBAC
│   │   │   └── seed.py          # First admin creation
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── trips.py
│   │   │   ├── receipts.py
│   │   │   ├── payments.py
│   │   │   ├── ledger.py
│   │   │   ├── reports.py       # PDF + Excel download
│   │   │   ├── rates.py
│   │   │   ├── vendors.py
│   │   │   ├── mills.py
│   │   │   └── users.py
│   │   └── services/
│   │       ├── pdf_service.py
│   │       └── excel_service.py
│   ├── alembic/                 # DB migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/               # Dashboard, Trips, Payments, Ledger...
│   │   ├── components/          # Layout, sidebar
│   │   ├── hooks/               # useAuth
│   │   └── utils/               # axios instance with JWT interceptor
│   └── Dockerfile
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Local Setup

**1. Clone and enter**
```bash
git clone <your-repo-url>
cd hisab
```

**2. Create environment file**
```bash
cp .env.example .env
```

Open `.env` and fill in:
- `POSTGRES_PASSWORD` — any strong password
- `SECRET_KEY` — run `python -c "import secrets; print(secrets.token_hex(32))"` and paste
- `FIRST_ADMIN_EMAIL` and `FIRST_ADMIN_PASSWORD` — your login credentials
- `COMPANY_NAME`, `COMPANY_GSTIN`, `COMPANY_ADDRESS`, `COMPANY_PHONE` — printed on PDFs

**3. Start everything**
```bash
docker compose up --build
```

First run takes 3–5 minutes. When you see:
```
hisab_backend | INFO: Uvicorn running on http://0.0.0.0:8000
```
the app is ready.

**4. Open in browser**

| URL | Purpose |
|---|---|
| `http://localhost:8080` | Main application |
| `http://localhost:8080/api/docs` | Swagger API docs (dev only) |

Login with `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD` from your `.env`.

---

## Daily Workflow

```
1. Daily Rates     → Set ₹/kg for each vendor and mill (morning)
2. New Trip        → Truck dispatched: tare + loaded weight → load weight for e-way bill
3. Mill Receipt    → Mill sends slip: enter net weight per material type
4. Payments        → Pay vendor balance, record mill receipts
5. Ledger          → Per-party full statement with date range
6. Reports         → Download GST invoice PDF or vendor receipt PDF
```

---

## Role Permissions

| Action | View only | Data entry | Admin |
|---|:---:|:---:|:---:|
| View dashboard, trips, ledger | ✓ | ✓ | ✓ |
| Create trip, enter receipt | | ✓ | ✓ |
| Create payment (draft) | | ✓ | ✓ |
| Submit payment for approval | | ✓ | ✓ |
| Approve / reject payment | | | ✓ |
| Confirm payment cleared | | | ✓ |
| Manual payment (skip workflow) | | | ✓ |
| Manage users | | | ✓ |

---

## Database Tables

| Table | Purpose |
|---|---|
| `users` | Login accounts with roles |
| `vendors` | Vendor master — name, GSTIN, bank, UPI |
| `mills` | Mill master — name, GSTIN, credit days |
| `daily_rates` | ₹/kg per vendor/mill per date |
| `trips` | Core entity — one row per truck trip |
| `mill_receipts` | Mill weighment slip per trip |
| `mill_receipt_lines` | Per-material lines within a receipt |
| `payments` | All payments with full workflow status |
| `invoices` | Generated PDF records |
| `audit_logs` | Every action — who, what, when |

---

## Phase 2 Roadmap

- [ ] E-way bill API (NIC portal — requires separate registration)
- [ ] Razorpay payment links → send via WhatsApp → auto-confirm on webhook
- [ ] Bank statement upload → auto-match incoming payments
- [ ] GSTR-1 export for monthly GST filing
- [ ] WhatsApp notifications for payment approvals