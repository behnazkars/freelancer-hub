# Architecture Decision Records

A log of significant technical decisions made during development.
Each entry explains the context, the decision, and the tradeoffs.

Format based on [Michael Nygard's ADR template](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).

---

## ADR-001 — FastAPI as the backend framework

**Date:** 2026-05  
**Status:** Active

**Context:**  
Needed a Python backend framework for a freelancer SaaS app. Options
considered: Flask, Django, FastAPI.

**Decision:**  
Chose FastAPI.

**Reasons:**
- Built-in Pydantic validation — request/response schemas are free
- Automatic Swagger UI at `/docs` — no extra tooling needed for API testing
- Modern async support for future scalability
- Type hints throughout — better IDE support and fewer runtime errors

**Consequences:**
- Less "batteries included" than Django — auth, admin had to be built manually
- Smaller ecosystem than Flask/Django but growing rapidly

---

## ADR-002 — Service layer architecture

**Date:** 2026-05  
**Status:** Active

**Context:**  
Needed to decide where business logic lives. Options: fat routers
(logic in routers), fat models (logic in models), or a separate service layer.

**Decision:**  
All business logic lives in `services/`. Routers are thin HTTP adapters only.

**Reasons:**
- Routers change when HTTP changes; services change when business rules change
- Services are testable without HTTP — no TestClient needed for unit tests
- Clear ownership — a new developer knows exactly where to look for logic

**Consequences:**
- More files than a simple fat-router approach
- Worth it at any scale beyond a simple prototype

---

## ADR-003 — JWT authentication (no sessions)

**Date:** 2026-05  
**Status:** Active

**Context:**  
Needed an auth strategy for a SaaS API. Options: server-side sessions,
JWT tokens, OAuth.

**Decision:**  
JWT tokens stored client-side, validated on every request.

**Reasons:**
- Stateless — no session store needed, scales horizontally
- Works naturally with both browser and API clients
- bcrypt for password hashing — industry standard cost factor

**Consequences:**
- Tokens cannot be invalidated before expiry (no logout blacklist)
- Acceptable tradeoff for this stage of the product

---

## ADR-004 — Ownership security on all queries

**Date:** 2026-05  
**Status:** Active

**Context:**  
Multi-tenant app where every user owns their own data. Risk of IDOR
(Insecure Direct Object Reference) — user A accessing user B's data by
guessing an ID.

**Decision:**  
Every database query filters by `user_id`. No exceptions.

**Reasons:**
- A user knowing `invoice/42` exists should not mean they can read it
- Defense in depth — even if a router bug exists, the service layer protects the data

**Consequences:**
- Every service function requires `user_id` as a parameter
- Slightly more verbose queries — worth it for the security guarantee

---

## ADR-005 — SQLite (dev) + PostgreSQL (prod)

**Date:** 2026-05  
**Status:** Active

**Context:**  
Needed a development database that requires zero setup and a production
database that is robust and scalable.

**Decision:**  
SQLite locally, PostgreSQL on Render in production. Same SQLAlchemy ORM
code targets both via `DATABASE_URL` environment variable.

**Reasons:**
- SQLite needs no installation — any developer can clone and run instantly
- PostgreSQL is the production standard for relational data
- SQLAlchemy abstracts the difference for most operations

**Consequences:**
- Raw SQL in migrations must be dialect-aware (SQLite vs PostgreSQL syntax differs)
- Some PostgreSQL features (e.g. JSONB, full-text search) are unavailable in SQLite
- Lesson learned: write dialect-aware migration SQL from the start

---

## ADR-006 — Alembic for database migrations

**Date:** 2026-06  
**Status:** Active — supersedes `Base.metadata.create_all()` for schema changes

**Context:**  
`Base.metadata.create_all()` creates missing tables but cannot modify
existing ones. As the schema evolves, a proper migration tool is needed.

**Decision:**  
Use Alembic with autogenerate. Run `alembic upgrade head` automatically
on startup in `main.py`.

**Reasons:**
- Tracks every schema change with a version history (like Git for the database)
- Autogenerate compares models to live schema and writes migration code
- Startup auto-run means production stays in sync after every deploy
- Idempotent — safe to run repeatedly, skips already-applied migrations

**Consequences:**
- Every model change needs a matching migration file committed to Git
- Developers must run `alembic upgrade head` after pulling schema changes locally
- Raw SQL migrations must handle SQLite/PostgreSQL dialect differences

---

## ADR-007 — Time tracking V2: start/end times replace hours float

**Date:** 2026-06  
**Status:** Active — supersedes the original `hours + date` design

**Context:**  
The original time entry model stored `hours: float` and `date: Date`.
This meant the user manually typed how many hours they worked — no actual
clock-in/clock-out data was captured.

**Problems with the old design:**
- No record of when work actually happened during the day
- Users could enter any float — no validation of real time boundaries
- `date` was a redundant field once real timestamps exist

**Decision:**  
Replace `hours + date` with `start_time`, `end_time`, and `duration`.
Duration is calculated server-side and stored — never accepted from the client.

**Reasons:**
- Richer data — actual clock-in/clock-out times are captured
- `duration` stored (not calculated on the fly) so analytics queries stay fast
- Pydantic `@model_validator` enforces `end_time > start_time` at the schema layer
- `date` is derivable from `start_time.date()` — no redundant field needed
- Frontend shows live duration preview as user picks times

**Consequences:**
- Required a database migration (ADR-006 pattern)
- Existing rows were backfilled with `09:00` start time as a best-guess placeholder
- Analytics service updated to use `duration` instead of `hours`
- All tests updated to use `start_time`/`end_time` instead of `hours`/`date`