# CLAUDE.md — Fundi Connect Backend

> AI-assistant guidelines and architecture standards for Fundi Connect.

## Overview

Fundi Connect is a verified informal-services marketplace for Kenya and East Africa. It connects households and SMEs with verified jua kali craftspeople and technicians (plumbers, electricians, appliance repairers, carpenters, mama fua, welders, painters) backed by safe **M-PESA escrow payments**.

## Architecture & Conventions

- **Application Factory Pattern**: `server/app.py` exposes `create_app(config_name)`.
- **API Versioning**: All endpoints are mounted with URL prefix `/api/v1/`.
- **Modular SQLAlchemy 2.0**: Models in `server/models/`, one file per domain.
- **Request Validation**: Marshmallow schemas in `server/schemas/` validate input boundaries before hitting services.
- **Service Layer**: Business logic lives in `server/services/`, keeping route blueprints thin and highly testable.
- **Money Representation**: Always stored and calculated as **integer minor units** (KES cents, e.g. 100 KES = 10000 cents). Never use floating point calculations for money.
- **Auth & RBAC**: Flask-JWT-Extended supporting `httpOnly` cookies and `Bearer` tokens. Roles: `customer`, `fundi`, `admin`. Decorators in `server/utils/auth.py`.
- **Escrow State Machine**: Safaricom Daraja STK Push collects and locks customer funds. Funds are released to Fundi wallet upon customer verification of job completion or handled through dispute arbitration.
- **File Length & Code Quality**: Modular design aiming for <300 lines per module. Clean Conventional Commits.

## Development Commands

```bash
# Setup Environment
cp .env.example .env
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run Development Server
flask --app server.wsgi:app run --port 5050

# Run Test Suite
pytest server/tests/ -v

# Code Quality / Linting
ruff check server/
ruff format server/

# Seed Database with Realistic Kenyan Data
python server/seed.py
```

## Security Standards

- **Rate Limiting**: Auth endpoints (login 5/min, register 3/min) and payments are strictly throttled.
- **CORS**: Configured strictly from `CORS_ORIGINS` environment variable.
- **Security Headers**: Enforced via `Flask-Talisman`.
- **Password Hashing**: Secure `bcrypt` hashes.
- **No Float Math**: Strict integer arithmetic for escrow, commissions, balances, and payouts.
