# ROADMAP.md — Fundi Connect

## Sprint 1: Backend Core & Escrow Engine (Current)
- [x] Application Factory, config validation, and database setup.
- [x] Data models: User, FundiProfile, Category, ServiceRequest, Quote, Booking, EscrowTransaction, Review, Dispute, Wallet, Message.
- [x] Auth system with JWT cookies/bearer & RBAC (`customer`, `fundi`, `admin`).
- [x] Safaricom Daraja STK Push & M-PESA Escrow state machine with local simulator.
- [x] Geo-location search (Haversine formula) for nearby fundis.
- [x] Full REST API under `/api/v1/` with Marshmallow validation.
- [x] Comprehensive pytest test suite & seed data for Kenyan market.

## Sprint 2: Frontend & Mobile Shell (Current)
- [x] React 19 + Vite + TypeScript frontend (hand-authored CSS design tokens rather than Tailwind).
- [x] Fundi discovery with estate, category, rating and GPS-radius filters.
- [x] Fundi onboarding: profile, skills, availability and national ID verification.
- [x] Booking timeline & live M-PESA STK push prompt with status polling.
- [x] Profile photos and account personalisation for every role.
- [x] Admin console: metrics, verification queue, dispute arbitration.
- [x] Mobile-first responsive layout.
- [x] Frontend deployed to Vercel; CI green on main.
- [x] Backend deployed to Render with a Neon PostgreSQL database.
- [ ] PWA installability and offline shell.
- [ ] Frontend test suite (Vitest + Playwright).

## Sprint 3: Trust, Moderation & Communications
- [ ] Verified Pro badge tiers and background check integration.
- [ ] Push notifications & SMS status updates (via Africa's Talking / Twilio).
- [ ] WhatsApp bot entry point for low-bandwidth informal workers.
- [ ] Automated dispute mediation SLAs.

## Sprint 4: Financial Services & Expansion
- [ ] Micro-insurance per job (cover accidental damages up to KES 50,000).
- [ ] Creditworthiness scoring integration for SACCO loans based on verified escrow job history.
- [ ] Expansion to Mombasa, Kisumu, Nakuru, and Eldoret.

## Sprint 5: Distribution ($0 path)

- [x] PWA layer, brand icons, assetlinks, privacy policy, Android TWA project
- [ ] Deploy → GitHub Release (APK) → Microsoft Store (PWABuilder) → Amazon / Samsung
- [ ] Google Play after the $25 registration (closed test: 12 testers, 14 days)
- [ ] In-app account deletion; switch from simulated to live Daraja; API keep-alive
