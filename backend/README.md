# NutriScan AI — Backend

The FastAPI backend powering NutriScan AI. It handles ingredient analysis, barcode lookups via Open Food Facts, personalised health scoring, user profiles, and scan history — all secured behind Firebase Authentication.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| Database ORM | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (async) |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/) |
| Local DB | SQLite via `aiosqlite` |
| Production DB | PostgreSQL 15 |
| Caching | Redis 7 |
| Auth | [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup) (JWT Bearer verification) |
| Rate Limiting | [slowapi](https://github.com/laurents/slowapi) |
| Testing | [pytest](https://docs.pytest.org/) + pytest-asyncio |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py               # FastAPI app, middleware, router registration
│   ├── core/
│   │   ├── config.py         # Pydantic Settings — loads from .env
│   │   ├── database.py       # SQLAlchemy async engine + session factory
│   │   ├── deps.py           # FastAPI dependency: get_current_user (Firebase)
│   │   ├── firebase.py       # Firebase Admin SDK initialisation
│   │   ├── cache.py          # Redis CacheClient (get_json / set_json)
│   │   └── rate_limit.py     # slowapi Limiter instance
│   ├── models/
│   │   ├── user.py           # User SQLAlchemy model
│   │   └── history.py        # ScanHistory SQLAlchemy model
│   ├── schemas/
│   │   ├── user.py           # UserProfileResponse, UserProfileUpdateRequest
│   │   ├── history.py        # ScanHistoryResponse, ScanHistoryCreateRequest
│   │   └── scan.py           # IngredientRequest, BarcodeRequest, ScanResponse
│   ├── routers/
│   │   ├── scan.py           # POST /scan/analyse, POST /scan/barcode
│   │   ├── user.py           # GET/PATCH/DELETE /users/me
│   │   └── history.py        # GET/DELETE /history, GET/DELETE /history/{id}
│   └── services/
│       ├── ingredient_engine.py  # Ingredient flag matching + Hₛ score algorithm
│       ├── nova_classifier.py    # NOVA group classification (1–4)
│       └── off_client.py         # Open Food Facts API HTTP client
├── alembic/                  # Database migration scripts
├── tests/                    # pytest test suite (13 tests)
├── .env.example              # Environment variable template
├── docker-compose.yml        # Postgres + Redis + API stack
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
└── API.md                    # Human-readable endpoint reference
```

---

## Local Setup (No Docker)

### 1. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt   # for testing
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in the required values. For local dev without Docker, the defaults work out of the box with SQLite — you only need to set `FIREBASE_CREDENTIALS_PATH`.

### 4. Set up Firebase credentials

1. Open the [Firebase Console](https://console.firebase.google.com/) and navigate to your NutriScan project.
2. Go to **Project Settings → Service Accounts**.
3. Click **Generate new private key** and download the JSON file.
4. Place it anywhere on your machine (outside the repo is recommended).
5. Set the path in `.env`:
   ```
   FIREBASE_CREDENTIALS_PATH=/absolute/path/to/serviceAccount.json
   ```

### 5. Apply database migrations

```bash
alembic upgrade head
```

This creates `nutriscan.db` (SQLite) on first run.

### 6. Generate a secret key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Paste the output as `SECRET_KEY` in your `.env`.

### 7. Run the development server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs (Swagger UI): `http://localhost:8000/docs`  
Alternative docs (ReDoc): `http://localhost:8000/redoc`

---

## Running with Docker Compose

The compose file starts **PostgreSQL 15**, **Redis 7**, and the **FastAPI service** together. Alembic migrations run automatically on container startup.

```bash
# First-time setup or after code changes
docker-compose up --build

# Subsequent runs (no rebuild needed)
docker-compose up
```

> **Important:** Before running with Docker, update `DATABASE_URL` in `.env` to use the Postgres connection string (it is pre-configured in `.env.example` as a comment):
> ```
> DATABASE_URL=postgresql+asyncpg://nutriuser:nutripass@db:5432/nutriscan
> ```

### Services exposed

| Service | Port |
|---|---|
| FastAPI backend | `http://localhost:8000` |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `PROJECT_NAME` | No | `NutriScan AI Backend` | Display name in API docs |
| `DATABASE_URL` | Yes | SQLite path | SQLAlchemy async connection string |
| `REDIS_URL` | Yes | `redis://redis:6379/0` | Redis connection string |
| `SECRET_KEY` | Yes | — | Cryptographic signing key (generate with `secrets.token_urlsafe(32)`) |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Token lifetime |
| `ENVIRONMENT` | No | `development` | `development`, `staging`, or `production` |
| `FIREBASE_PROJECT_ID` | Yes | — | Your Firebase project ID |
| `FIREBASE_CREDENTIALS_PATH` | Yes | — | Absolute path to Firebase service account JSON |

---

## API Endpoints Overview

Full details in [`API.md`](./API.md). Interactive spec at `/docs` when the server is running.

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/scan/analyse` | Optional | Analyse raw ingredient list; saves to history if authenticated |
| `POST` | `/scan/barcode` | Optional | Look up product by barcode via Open Food Facts |
| `GET` | `/users/me` | Required | Get current user's profile (auto-creates on first call) |
| `PATCH` | `/users/me` | Required | Partially update allergies / conditions / goals |
| `DELETE` | `/users/me` | Required | Delete account and all scan history |
| `GET` | `/history` | Required | List scan history (paginated, newest first) |
| `GET` | `/history/{id}` | Required | Get a single past scan |
| `DELETE` | `/history/{id}` | Required | Delete a specific past scan |
| `DELETE` | `/history` | Required | Clear all scan history |
| `GET` | `/health` | None | DB + Redis health check (for readiness probes) |

Authentication uses Firebase ID tokens sent as `Authorization: Bearer <token>`.

---

## Core Services

### `ingredient_engine.py`
Accepts a list of raw ingredient strings and:
- Matches against a database of E-codes, banned additives, and flagged keywords using fuzzy matching (`rapidfuzz`).
- Calculates the personalised **Hₛ (Health Safety) score** (0–100), applying deductions for allergens, NOVA group, additive risk, health conditions (Diabetes, Hypertension, High Cholesterol), and nutrient macros.

### `nova_classifier.py`
Classifies ingredient lists into [NOVA groups](https://world.openfoodfacts.org/nova) (1 = minimally processed → 4 = ultra-processed) using keyword matching.

### `off_client.py`
Thin async HTTP client wrapping the [Open Food Facts v2 API](https://wiki.openfoodfacts.org/API). Used by `POST /scan/barcode` to fetch product data by barcode.

---

## Performance & Rate Limiting

- **Rate Limiting:** `/scan/analyse` and `/scan/barcode` are limited to **30 requests/minute per IP** using `slowapi`. Exceeding this returns `HTTP 429`.
- **Redis Caching:** A `CacheClient` is defined in `core/cache.py` for 24-hour JSON caching. Currently wired to the `/health` check — planned for use with OFF barcode lookups in a future iteration.

---

## Testing

```bash
# Run the full test suite
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_scan.py -v
```

Current coverage: **13 tests, 13 passed**.

Tests use an in-memory SQLite database and mock Firebase auth — no real Firebase credentials are needed to run them.

---

## Known Issues / Open Items

- `backend/nutriscan.db.bak` is currently tracked by git. Run `git rm --cached backend/nutriscan.db.bak` to untrack it.
- `POST /history` endpoint is not yet implemented — the mobile app expects it for offline scan sync. A router entry needs to be added to `routers/history.py` with the `ScanHistoryCreateRequest` schema.
- Redis caching for OFF barcode lookups is defined but not yet called from routers.
- Pydantic V2 deprecation warning: `Settings` uses class-based config. Migrate to `model_config = SettingsConfigDict(...)` in a future cleanup.
