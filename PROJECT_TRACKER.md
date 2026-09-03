# Project Tracker — Fundi Connect

| Date | Milestone / Task | Status | Notes |
|---|---|---|---|
| 2026-09-01 | Architecture design & implementation plan | Completed | Defined M-PESA escrow engine, schema, and API map |
| 2026-09-01 | Repo scaffold, docs, Docker, config | Completed | Flask 3, pyproject, requirements, .env.example |
| 2026-09-01 | Core domain models & schemas | Completed | User, FundiProfile, Escrow, Booking, Dispute, Wallet, Conversation |
| 2026-09-01 | Services & escrow state machine | Completed | Daraja integration, escrow release/refund, geo search |
| 2026-09-01 | REST route blueprints (`/api/v1`) | Completed | 13 domain blueprints with Marshmallow validation |
| 2026-09-01 | Kenyan seed data script | Completed | Nairobi estates, 6 fundis, requests, bookings, escrow |
| 2026-09-01 | Pytest suite | Completed | 31 tests green |
| 2026-09-03 | Backend security & correctness audit | Completed | Fixed unauthenticated escrow funding, unverified webhook amounts, unused prod config validation, float commission math, sub-shilling truncation, unlocked wallet debits. 47 tests |
| 2026-09-03 | Missing API endpoints | Completed | `POST /auth/refresh`, notifications feed, paginated fundi search |
| 2026-09-03 | Frontend rebuild (React 19 + TS) | Completed | Replaced mock-data shell with typed client covering customer, fundi and admin journeys |
| 2026-09-03 | Profile personalisation | Completed | Avatars (Cloudinary with link fallback), profile & account settings for every role |
| 2026-09-03 | Admin console | Completed | Metrics, fundi verification queue, dispute arbitration |
| 2026-09-03 | CI + Dependabot | Completed | Backend lint/tests, frontend lint/typecheck/build, advisory audit. Green on main |
| 2026-09-03 | Frontend deploy (Vercel) | Completed | <https://fundi-connect-pi.vercel.app> |
| 2026-09-03 | Backend deploy (Render) | Completed | <https://fundi-connect-api.onrender.com> — Neon Postgres (eu-central-1), demo data seeded on first boot |
| 2026-09-03 | End-to-end verification on production | Completed | Login → search → booking → STK push → escrow funded, driven through the live site on a phone viewport |
| — | Alembic migrations | Pending | `flask init-db` is the interim; cannot alter existing tables |
| — | Frontend test suite | Pending | Currently covered by typecheck, lint and build only |

## Sprint summary — 2026-09-03

Audited the backend and found six issues that could move or lose money, the most
serious being an unauthenticated `simulate-callback` endpoint that let anyone mark
an escrow as funded. All fixed with regression tests.

Rebuilt the frontend from an 833-line mock-data prototype into a feature-organised
TypeScript app wired to the real API, and verified the full booking → escrow →
release → review journey through the browser on a phone viewport.

Published the repo, deployed the web app, and set up CI — which immediately earned
its keep by catching that `.gitignore` had been silently excluding `frontend/src/lib`.
