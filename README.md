# Fundi Connect

> **Verified informal-services marketplace with M-PESA escrow** for Kenya and East Africa.

Fundi Connect bridges the trust gap in Kenya's informal (*jua kali*) economy. It connects households and businesses with verified craftspeople — plumbers, electricians, phone and appliance repair techs, carpenters, masons, painters, mama fua, welders — backed by identity verification, geo-search, transparent ratings, and **automated M-PESA escrow protection**.

The trust anchor is the escrow: a customer's money is locked with the platform, not handed to the fundi, and is only released when the customer confirms the job — or when an admin arbitrates a dispute.

---

## Live demo

| Surface | URL | Status |
|---|---|---|
| **Web app** (Vercel) | <https://fundi-connect-pi.vercel.app> | Live |
| **API** (Render) | <https://fundi-connect-api.onrender.com> | Live |
| **API health** | <https://fundi-connect-api.onrender.com/api/health> | Live |
| **Repository** | <https://github.com/gnm7208/fundi-connect> | Public |

> **First load can take ~50 seconds.** The API runs on Render's free tier, which sleeps after 15 minutes idle; the next request wakes it. Once awake it is fast.
>
> The public demo runs with **simulated M-PESA payments** — the app says so in a banner, and `/api/health` reports `"payments": "simulated"`. No real money moves.

### Demo accounts

All seeded accounts use the password `fundi123`.

| Role | Email |
|---|---|
| Customer | `sarah.kimani@gmail.com` |
| Fundi (plumber) | `john.mwangi@fundi.co.ke` |
| Fundi (electrician) | `otieno.sparks@fundi.co.ke` |
| Admin | `admin@fundiconnect.co.ke` |

---

## Install as an app

Fundi Connect is a Progressive Web App. The web build in `frontend/` is also what ships to the app stores — there is no separate mobile codebase.

| Platform | How |
|---|---|
| **Android / desktop Chrome** | Open <https://fundi-connect-pi.vercel.app> → browser menu → **Install app** (or **Add to Home screen**). |
| **Android APK** | Download the latest signed APK from [GitHub Releases](https://github.com/gnm7208/fundi-connect/releases) and open it (allow "install from this source" once). |
| **Microsoft Store** | Listed as **Fundi Connect** (packaged from the PWA with PWABuilder). |
| **Google Play / Amazon / Samsung** | Same Android package (`com.gnm7208.fundiconnect`); listings go live per store — check Releases for status. |

Privacy policy: <https://fundi-connect-pi.vercel.app/privacy.html> (also linked from every store listing; deletion requests are handled by email as described there).

**How it works.** `frontend/public/manifest.webmanifest` declares the app (name, colours, PNG + maskable icons), `frontend/public/sw.js` caches the app shell so it opens with no signal (API responses are deliberately never cached), and `frontend/src/lib/register-sw.ts` registers the worker in production builds only. `frontend/public/.well-known/assetlinks.json` links the site to the Android signing key so the Android app opens full-screen without browser chrome; the Android project itself lives outside this repo in `../store-packaging/` (Bubblewrap TWA) and the signing key in `~/.android-signing/` — never commit either.

## Key features

1. **Verified fundi profiles** — national ID verification reviewed by an admin, skill catalogue, service radius, ratings, and profile photos.
2. **Geo-location search** — find nearby technicians by estate (Kilimani, Westlands, Eastleigh, Roysambu, Karen) or GPS distance, with a SQL bounding-box prefilter refined by the Haversine formula.
3. **Flexible job matching** — book a fundi directly, or post a job and compare competitive quotes.
4. **M-PESA escrow** — STK Push locks the customer's funds; the fundi works knowing the money is there; the customer confirms and escrow releases to the fundi's wallet minus the platform fee.
5. **Dispute arbitration** — either party can freeze an escrowed job; an admin decides refund or payout.
6. **Fundi wallets** — commission ledger and instant M-PESA B2C payout requests.
7. **In-app messaging and notifications** — per-booking conversations and a notification feed.
8. **Installable app** — a PWA with an offline app shell, packaged for Android (TWA) and the Microsoft Store from the same build; see [Install as an app](#install-as-an-app).

---

## Tech stack

**Backend** — Python 3.12, Flask 3 (app factory), SQLAlchemy 2.0, Marshmallow validation at the API boundary, Flask-JWT-Extended (httpOnly cookies + Bearer tokens) with RBAC, Safaricom Daraja (STK Push C2B + B2C payouts) with a local simulator, Flask-Talisman, Flask-Limiter, pytest.

**Frontend** — React 19, Vite, TypeScript (strict), TanStack Query for server state, React Router, hand-authored CSS design-token system with light/dark themes, `prefers-reduced-motion` support, and a mobile-first layout built for the Android hardware this market runs on.

### Money representation

All money is stored and calculated as **integer minor units** (KES cents). The platform commission is held as integer **basis points** so no float ever touches a monetary calculation, and the fundi is paid the exact remainder — fee + payout always reconstructs the amount the customer escrowed. Amounts are constrained to whole shillings at the API boundary, because M-PESA cannot move fractions of a shilling.

---

## Quickstart

### Backend

```bash
cp .env.example .env
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python server/seed.py                              # realistic Kenyan demo data
flask --app server.wsgi:app run --port 5050
```

API at `http://localhost:5050`, health at `http://localhost:5050/api/health`.

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

App at `http://localhost:5173`. In development the Vite dev server proxies `/api` to the Flask API, keeping requests same-origin so the auth cookies work.

### Optional: profile photo uploads

Avatar uploads go direct to Cloudinary. Without configuration the app degrades gracefully to pasting an image link, so this is optional:

```bash
# frontend/.env
VITE_CLOUDINARY_CLOUD_NAME=your_cloud
VITE_CLOUDINARY_UPLOAD_PRESET=your_unsigned_preset
```

---

## API overview (mounted at `/api/v1`)

| Domain | Routes |
|---|---|
| **Auth** | `POST /auth/register` · `POST /auth/login` · `POST /auth/refresh` · `POST /auth/logout` · `GET/PATCH /auth/me` |
| **Categories** | `GET /categories` · `GET /categories/<slug>` · `POST/PATCH` (admin) |
| **Fundis** | `GET /fundis/search` · `GET /fundis/<id>` · `PATCH /fundis/profile` · `POST/DELETE /fundis/skills` · `POST /fundis/verify-id` |
| **Service requests** | `GET/POST /service-requests` · `GET /service-requests/<id>` · `POST /service-requests/<id>/quotes` · `POST /service-requests/<id>/quotes/<qid>/accept` |
| **Bookings** | `GET/POST /bookings` · `GET /bookings/<id>` · `PATCH /bookings/<id>/status` · `POST /bookings/<id>/confirm` |
| **Payments & escrow** | `POST /payments/stk-push` · `POST /payments/daraja/callback` · `GET /payments/status/<id>` · `GET /escrow/booking/<id>` |
| **Reviews** | `POST /reviews` · `GET /reviews/fundi/<id>` |
| **Disputes** | `POST /disputes` · `GET /disputes/<id>` · `POST /disputes/<id>/respond` |
| **Wallets** | `GET /wallets/me` · `GET /wallets/me/transactions` · `POST /wallets/payout-request` |
| **Conversations** | `GET/POST /conversations` · `GET /conversations/<id>` · `POST /conversations/<id>/messages` |
| **Notifications** | `GET /notifications` · `POST /notifications/<id>/read` · `POST /notifications/read-all` |
| **Admin** | `GET /admin/metrics` · `GET /admin/fundis/pending-verification` · `PATCH /admin/fundis/<id>/verify` · `GET /admin/disputes` · `POST /admin/disputes/<id>/resolve` |

### Escrow state machine

```text
booking:  pending → accepted_unpaid → escrow_funded → in_progress → awaiting_confirm → completed
                                                   ↘ disputed ↗
escrow:   pending → held_in_escrow → released (to fundi) | refunded (to customer)
```

---

## Deployment

The backend deploys to **Render** from `render.yaml` (a Blueprint that also provisions PostgreSQL), and the frontend to **Vercel** from `frontend/vercel.json`.

### 1. Backend on Render

1. Go to <https://dashboard.render.com/blueprints> → **New Blueprint Instance** → pick this repo.
2. Render reads `render.yaml` and creates the web service plus a free PostgreSQL database. `SECRET_KEY` and `JWT_SECRET_KEY` are generated automatically.
3. Fill in the variables marked `sync: false`:
   - `CORS_ORIGINS` — your Vercel URL — `https://fundi-connect-pi.vercel.app`. Without this the browser blocks every API call.
   - `DARAJA_*` — your Safaricom Daraja sandbox credentials, if running live payments.

   The live deployment uses an external **Neon** PostgreSQL instance rather than the
   blueprint's database, because Render allows only one free database per account.
   To do the same, create a Neon project and set `DATABASE_URL` to its pooled
   connection string; Neon's free tier does not expire after 30 days the way
   Render's does.
4. For a **public demo** with simulated payments, also set `DARAJA_SIMULATION_MODE=true` and `ALLOW_SIMULATED_PAYMENTS=true`. Production config refuses to boot with simulated payments unless that second flag is set deliberately.
5. Demo data seeds itself on first boot — the start command runs `flask seed-demo`, which only populates an empty database (free plans have no shell to run a script from).

The start command runs `flask init-db` before Gunicorn, which creates any missing tables (this project has no Alembic migrations yet — see [Known gaps](#known-gaps)).

### 2. Frontend on Vercel

```bash
cd frontend
vercel --prod
```

Set one environment variable in the Vercel project:

```bash
VITE_API_BASE_URL=https://<your-render-service>.onrender.com/api/v1
```

Because the deployed frontend and API are on different origins, the app authenticates with Bearer tokens rather than cookies; this is handled automatically by the API client.

---

## Testing & quality

```bash
pytest server/tests -q       # 47 tests
ruff check server/           # lint
ruff format server/          # format

cd frontend
npm run lint                 # oxlint
npx tsc -b                   # strict typecheck
npm run build                # production build
```

CI runs all of the above on every push and pull request (`.github/workflows/ci.yml`), plus an advisory dependency audit.

---

## Security notes

- **Rate limits** — register 3/min, login 5/min, STK push 10/min, payouts 5/min.
- **Escrow integrity** — a short M-PESA payment never funds a job; the webhook amount is verified against the escrow record before funds are marked as held.
- **Payment simulation** is authenticated, restricted to the paying customer, and disabled outside simulation mode.
- **Production config validation** runs at boot: missing secrets, or simulated payments without an explicit demo opt-in, refuse to start.
- **Passwords** are bcrypt-hashed; ID numbers and admin verification notes are never returned by public endpoints.
- **CORS** is restricted to `CORS_ORIGINS`; security headers via Flask-Talisman.

---

## Known gaps

- **No Alembic migrations.** Schema is created by `flask init-db`, which cannot alter existing tables. Adding migrations is the next infrastructure task.
- **Rate-limit storage is in-memory**, so limits are per-process. Move to Redis before running multiple workers.
- **No frontend test suite yet** — the backend has 47 tests; the client is covered by typecheck, lint and build only.

---

## License

MIT License (c) 2026 George
