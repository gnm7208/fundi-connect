# ROADMAP.md — Fundi Connect

## Sprint 1: Backend Core & Escrow Engine (Current)
- [x] Application Factory, config validation, and database setup.
- [x] Data models: User, FundiProfile, Category, ServiceRequest, Quote, Booking, EscrowTransaction, Review, Dispute, Wallet, Message.
- [x] Auth system with JWT cookies/bearer & RBAC (`customer`, `fundi`, `admin`).
- [x] Safaricom Daraja STK Push & M-PESA Escrow state machine with local simulator.
- [x] Geo-location search (Haversine formula) for nearby fundis.
- [x] Full REST API under `/api/v1/` with Marshmallow validation.
- [x] Comprehensive pytest test suite & seed data for Kenyan market.

## Sprint 2: Frontend & Mobile Shell
- [ ] React 19 + Vite + Tailwind CSS frontend with TypeScript.
- [ ] Fundi discovery map and estate search filters.
- [ ] Fundi onboarding flow with national ID upload.
- [ ] Booking timeline & live M-PESA STK push prompt.
- [ ] Mobile responsiveness & PWA installability.

## Sprint 3: Trust, Moderation & Communications
- [ ] Verified Pro badge tiers and background check integration.
- [ ] Push notifications & SMS status updates (via Africa's Talking / Twilio).
- [ ] WhatsApp bot entry point for low-bandwidth informal workers.
- [ ] Automated dispute mediation SLAs.

## Sprint 4: Financial Services & Expansion
- [ ] Micro-insurance per job (cover accidental damages up to KES 50,000).
- [ ] Creditworthiness scoring integration for SACCO loans based on verified escrow job history.
- [ ] Expansion to Mombasa, Kisumu, Nakuru, and Eldoret.
