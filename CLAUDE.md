# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Generate a bcrypt hash for a new admin user (edit credentials in script first)
python create_admin.py
```

There are no automated tests in this project.

## Architecture

This is a single-file Flask REST API (`app.py`) backed by MySQL. All routes, middleware, and DB logic live in that one file.

**Database**: MySQL tables are created manually via phpMyAdmin — no migrations or ORM. Two tables:
- `users` — id, username, password_hash (bcrypt), is_admin, created_at
- `sessions` — token (UUID), user_id (FK), created_at, expires_at (7-day TTL)

**Authentication layers** — two independent decorators:
- `@require_auth` — validates `Authorization: Bearer <token>` against the `sessions` table, attaches user to `request.current_user`
- `@require_admin_token` — validates `x-admin-token` header against `ADMIN_API_KEY` env var

**Route groups**:
- `GET /`, `GET /health` — public health checks
- `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` — session auth (login rate-limited to 5/min)
- `POST|GET /admin/users`, `DELETE /admin/users/<id>`, `PATCH /admin/users/<id>/password` — admin-key protected

**Deployment**: cPanel WSGI. The `application = app` alias at the top of `app.py` is required by cPanel's WSGI entry point. `PORT` env var is only used for local dev; cPanel ignores it.

## Environment

Copy `.env` and populate all required vars before running locally:

```
DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
ADMIN_API_KEY   # secret for all /admin/* endpoints
CORS_ORIGINS    # comma-separated origins, or * for all (default)
PORT            # local dev only, default 5000
```

Two virtual envs exist (`.venv/` and `venv/`) — use whichever is active. `.venv` is the newer one.

## Adding a new admin user

Run `create_admin.py` (edit username/password first) to generate a bcrypt hash and SQL `INSERT` statement, then paste it into phpMyAdmin.
