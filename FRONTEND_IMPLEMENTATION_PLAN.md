# Frontend Implementation Plan — Fundi Connect

## Status check

The backend is functionally complete for the current scope.

Verified evidence:
- Python 3.12 runtime is the supported version for this project.
- The backend test suite passes under that runtime:
  - `pytest server/tests -q`
  - Result: `31 passed in 9.34s`

This means the frontend work can proceed without needing to block on backend feature gaps.

---

## Goal

Build the customer-facing, fundi-facing, and admin frontend for the Fundi Connect platform in a way that matches the existing Flask API contracts and the Kenyan informal-services marketplace flow.

---

## Recommended frontend stack

- React 19
- Vite
- TypeScript
- Tailwind CSS
- React Router
- Axios or Fetch client with a shared API layer
- Zustand or React Context for auth/session state
- Mobile-first design with PWA support
- Optional: Leaflet / mapbox for geo-search and nearby fundis

---

## Architecture approach

### 1. App structure

```text
client/
  src/
    app/
      App.tsx
      routes.tsx
      providers/
    features/
      auth/
      home/
      fundis/
      bookings/
      payments/
      disputes/
      wallet/
      admin/
    components/
      layout/
      forms/
      cards/
      modals/
      maps/
    lib/
      api.ts
      auth.ts
      storage.ts
      formatters.ts
    styles/
      globals.css
      theme.css
    types/
      api.ts
```

### 2. API integration patterns

- Centralize all backend calls in `src/lib/api.ts`.
- Use a typed response layer for auth, user, booking, payment, wallet, and dispute endpoints.
- Add shared request/response interceptors for JWT auth and error handling.
- Keep route-level pages thin and move business logic into feature hooks or services.

---

## Delivery plan

### Phase 0 — Project setup and bootstrap

Tasks:
- Initialize Vite React + TypeScript app under `client/`.
- Add Tailwind, shadcn/ui-style component patterns, and project aliases.
- Configure environment variables for API URL and app metadata.
- Set up linting, formatting, and test tooling.

Acceptance criteria:
- App boots locally.
- Environment-based API configuration works.
- Base theme, layout shell, and route scaffolding exist.

---

### Phase 1 — Authentication and onboarding

Tasks:
- Register and login screens.
- Role-based auth flow for `customer`, `fundi`, and `admin`.
- Session persistence with secure cookies/token handling.
- Profile completeness check and onboarding steps.
- Fundi verification flow for ID upload and profile completion.

Acceptance criteria:
- Users can register and log in as each role.
- Protected routes redirect correctly.
- Fundi onboarding matches the backend profile schema.

---

### Phase 2 — Customer experience

Tasks:
- Landing page and category browsing.
- Nearby fundi search by estate and radius.
- Fundi detail cards with skills, rating, pricing, and reviews.
- Service request creation and quote flow.
- Booking creation and status tracking.
- Review submission after job completion.

Acceptance criteria:
- A customer can search, select, and book a fundi.
- Service requests, booking state, and review flows work end-to-end.
- Mobile-first UI is usable on common phone sizes.

---

### Phase 3 — Fundi experience

Tasks:
- Fundi dashboard with earnings, open jobs, and profile status.
- Booking accept/decline and status updates.
- Start, complete, and confirmation flows.
- Wallet dashboard and payout request form.
- Messaging UI for conversations tied to bookings.

Acceptance criteria:
- A fundi can review incoming jobs and update statuses.
- Wallet balance and payout actions reflect backend data accurately.
- Conversations and booking updates feel instantaneous and readable.

---

### Phase 4 — Payment and trust UX

Tasks:
- M-PESA STK push flow UX with loading states and clear trust messaging.
- Escrow status screen and timeline.
- Dispute submission and admin status tracking.
- Success/error banners and confirmation states.

Acceptance criteria:
- Users understand payment lock/release flow without confusion.
- Escrow and dispute pages are explicit and easy to follow.
- Payment states reflect backend response data reliably.

---

### Phase 5 — Admin operations

Tasks:
- Admin dashboard with platform metrics.
- Verification approval actions for fundis.
- Dispute resolution and case review screens.
- Category and content moderation management.

Acceptance criteria:
- Admin can action verification and dispute tasks without backend workarounds.
- Metrics dashboard is readable and action-oriented.

---

### Phase 6 — Production polish and deployment

Tasks:
- PWA manifest, installability, offline-ready shell.
- Responsive design QA for Kenya device sizes.
- Image optimization and lazy loading.
- Error boundaries and loading skeletons.
- Deploy to Vercel / Netlify / hosting platform with API proxy config.

Acceptance criteria:
- App installs and behaves like a mobile app on supported devices.
- UX remains stable across common breakpoints.
- Production build is clean and deployable.

---

## Suggested implementation order

1. Frontend scaffold and base design system
2. Auth + protected routing
3. Customer search and booking flow
4. Fundi dashboard and job management
5. Wallet, escrow, disputes, and review flows
6. Admin tools
7. PWA polish and deployment

---

## Risk areas to watch

- JWT/session expiry and redirect loops
- Payment flow UX mismatches with backend callback delays
- Geo search and map performance for large result sets
- Messaging timeline consistency across bookings and service requests
- Role-specific route guard logic for `customer`, `fundi`, and `admin`

---

## Definition of done

The frontend is considered done when:
- All core user journeys are implemented and tested.
- The app matches the API behavior of the backend.
- Customer, fundi, and admin flows are all functional.
- The human-facing UX is mobile-first and production-ready.
- The app is buildable and deployable without unresolved blockers.

---

## Recommended next immediate step

Start by scaffolding the React app in a dedicated `client/` folder and implement the auth + protected route shell first. This gives the rest of the customer and fundi flows a stable base and keeps the project aligned with the already-complete backend.
