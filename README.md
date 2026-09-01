# Fundi Connect

> **Verified informal-services marketplace with M-PESA escrow** for Kenya and East Africa.

Fundi Connect bridges the trust gap in Kenya's informal (*jua kali*) economy. It connects households and businesses with verified craftspeople (plumbers, electricians, phone/appliance repair techs, carpenters, masons, painters, mama fua, welders) backed by identity verification, geo-search, transparent ratings, and **automated M-PESA escrow protection**.

---

## Key Features

1. **Verified Fundi Profiles & Skills**: National ID / certification verification, skill catalogue, portfolio, service radius, and client reviews.
2. **Geo-Location Search**: Find nearby technicians by estate (e.g. Kilimani, Westlands, Eastleigh, Roysambu, Karen) or GPS distance (Haversine formula).
3. **Flexible Job Matching**: Direct bookings or competitive quotes on customer service requests.
4. **M-PESA Escrow Trust Anchor**:
   - Customer initiates payment via Safaricom Daraja STK Push.
   - Funds are locked safely in escrow.
   - Fundi delivers the service.
   - Customer confirms completion -> Escrow releases earnings to Fundi wallet minus platform fee.
5. **Fair Dispute Arbitration**: Structured dispute resolution with admin mediation and refund/release controls.
6. **Fundi Earnings & Wallets**: Track completed jobs, commission ledger, and instant M-PESA B2C payout requests.
7. **In-App Messaging**: Real-time communication between customers and fundis per service request or booking.

---

## Tech Stack

- **Framework**: Python 3.12, Flask 3.x (App Factory Pattern)
- **Database & ORM**: PostgreSQL / SQLite, SQLAlchemy 2.0, Alembic
- **Validation**: Marshmallow schemas at the API boundary
- **Authentication**: Flask-JWT-Extended (`httpOnly` cookies + `Bearer` tokens) with RBAC (`customer`, `fundi`, `admin`)
- **Payments**: Safaricom Daraja API (STK Push C2B, Payout B2C) + local sandbox simulator
- **Security**: Flask-Talisman (CSP / security headers), Flask-Limiter (rate limits), Flask-CORS
- **Testing**: Pytest suite with isolated test clients and fixtures

---

## Quickstart

### 1. Prerequisites
- Python 3.12+
- Docker & Docker Compose (optional for local PostgreSQL)

### 2. Setup

```bash
# Clone and enter directory
cd "Fundi Connect"

# Copy environment variables
cp .env.example .env

# Create and activate virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database & Seed Data

```bash
# Seed realistic Kenyan demo data (locations, fundis, requests, bookings, escrow)
python server/seed.py
```

### 4. Run Server

```bash
flask --app server.wsgi:app run --port 5050
```

The API will be available at `http://localhost:5050`. Check health at:
`http://localhost:5050/api/health`

---

## API Overview (Mounted at `/api/v1`)

| Domain | Routes | Description |
|---|---|---|
| **Auth** | `POST /auth/register`<br>`POST /auth/login`<br>`POST /auth/logout`<br>`GET /auth/me`<br>`PATCH /auth/me` | Register as customer or fundi, login, get current session profile |
| **Categories** | `GET /categories`<br>`POST /categories`<br>`GET /categories/<slug>` | Browse skill categories and standard pricing guidance |
| **Fundis** | `GET /fundis/search`<br>`GET /fundis/<id>`<br>`PATCH /fundis/profile`<br>`POST /fundis/verify-id` | Geo search by radius/skill, view profile, update services, submit ID |
| **Service Requests** | `GET /service-requests`<br>`POST /service-requests`<br>`POST /service-requests/<id>/quotes`<br>`POST /service-requests/<id>/quotes/<qid>/accept` | Post RFQs, submit quotes, accept quotes |
| **Bookings** | `GET /bookings`<br>`POST /bookings`<br>`GET /bookings/<id>`<br>`PATCH /bookings/<id>/status`<br>`POST /bookings/<id>/confirm` | Direct booking, accept/decline, start, complete, confirm |
| **Payments & Escrow** | `POST /payments/stk-push`<br>`POST /payments/daraja/callback`<br>`GET /escrow/<booking_id>` | Initiate M-PESA escrow funding, webhook callbacks, escrow status |
| **Reviews** | `POST /reviews`<br>`GET /fundis/<id>/reviews` | Submit verified review after escrow completion, list reviews |
| **Disputes** | `POST /disputes`<br>`GET /disputes/<id>`<br>`POST /disputes/<id>/respond` | File dispute on escrowed booking, submit response |
| **Wallets** | `GET /wallets/me`<br>`GET /wallets/me/transactions`<br>`POST /wallets/payout-request` | Fundi balance, commission ledger, M-PESA payout request |
| **Conversations** | `GET /conversations`<br>`POST /conversations`<br>`POST /conversations/<id>/messages` | In-app messaging between customer and fundi |
| **Admin** | `GET /admin/metrics`<br>`PATCH /admin/fundis/<id>/verify`<br>`POST /admin/disputes/<id>/resolve` | Platform GMV, fundi verification approval, dispute arbitration |

---

## Testing & Quality

```bash
# Run all tests
pytest server/tests/ -v

# Run linter
ruff check server/
```

---

## License

MIT License (c) 2026 George
