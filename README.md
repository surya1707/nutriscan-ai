# NutriScan AI

> **Decode what you eat.** — A full-stack, cross-platform food intelligence platform that analyses ingredient labels, classifies food processing levels, and delivers a personalised health score matched to your allergies, conditions, and dietary goals.

---

## Monorepo Structure

```
nutriscan-ai/
├── backend/          # FastAPI REST API — ingredient analysis, auth, history
├── mobile/           # Flutter app (iOS & Android)
├── web/              # React + Vite web app
└── docs/             # Architecture diagrams & API specs
```

---

## Tech Stack

### Backend — `backend/`

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI (async) |
| Database | PostgreSQL 15 (prod) / SQLite (local dev) |
| ORM | SQLAlchemy 2 (async) + Alembic migrations |
| Auth | Firebase Admin SDK (JWT verification) |
| Rate limiting | SlowAPI + Redis |
| Containerisation | Docker + Docker Compose |
| External data | Open Food Facts API (barcode lookup) |

### Web App — `web/`

| Layer | Technology |
|---|---|
| Language | TypeScript |
| Framework | React 19 |
| Bundler | Vite 8 |
| Styling | Tailwind CSS v4 (`@tailwindcss/vite`) |
| Routing | React Router v7 |
| Global state | Zustand |
| HTTP client | Axios |
| Auth | Firebase JS SDK v11 (Google sign-in, email magic-link, guest mode) |

### Mobile App — `mobile/`

| Layer | Technology |
|---|---|
| Language | Dart |
| Framework | Flutter |
| State | Riverpod |
| Routing | GoRouter |
| Storage | Drift (SQLite, local-only) |
| Auth | Firebase Auth |

### Design System

All three surfaces share the same design tokens, sourced from `mobile/lib/core/theme/app_theme.dart`:

| Token | Hex |
|---|---|
| `cream` (background) | `#F5F2EC` |
| `darkGreen` (primary) | `#2D4A3E` |
| `mediumGreen` (accent) | `#4A7C6F` |
| `lightGreen` (subtle) | `#D6E4DF` |
| `safeGreen` | `#2D8653` |
| `flaggedRed` | `#D94F3D` |
| `cautionAmber` | `#E5A020` |
| `textPrimary` | `#1A1A1A` |
| `textSecondary` | `#6B6B6B` |
| `textMuted` | `#9E9E9E` |

---

## Quick Start

### Prerequisites

- **Docker Desktop** (recommended for the full stack)
- **Node.js 20+** and **npm** (for web)
- **Python 3.11+** and **pip** (for backend, local dev only)
- **Flutter SDK 3.x** (for mobile)
- A **Firebase project** with Authentication enabled (Google provider + Email link)

---

### 1 — Backend

#### Option A: Docker (recommended — zero setup)

```bash
cd backend
cp .env.example .env        # edit FIREBASE_PROJECT_ID and SECRET_KEY
docker compose up --build
```

The API starts at **http://localhost:8000**.  
Interactive docs: **http://localhost:8000/docs**

Docker Compose starts three services:

| Service | Port | Purpose |
|---|---|---|
| `api` | 8000 | FastAPI (auto-runs `alembic upgrade head` on start) |
| `db` | 5432 | PostgreSQL 15 |
| `redis` | 6379 | Rate-limit store |

#### Option B: Local Python (SQLite, no Docker)

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# DATABASE_URL is already set to SQLite in .env.example — no changes needed for local dev

alembic upgrade head           # creates nutriscan.db + tables

uvicorn app.main:app --reload  # starts on http://localhost:8000
```

#### Backend Environment Variables (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | SQLite (`sqlite+aiosqlite:///./nutriscan.db`) or Postgres (`postgresql+asyncpg://...`) |
| `REDIS_URL` | ✅ | `redis://localhost:6379/0` (local) or `redis://redis:6379/0` (Docker) |
| `SECRET_KEY` | ✅ | Random string — used for token signing |
| `FIREBASE_PROJECT_ID` | ✅ | Your Firebase project ID |
| `FIREBASE_CREDENTIALS_PATH` | ✅ | Absolute path to Firebase service-account JSON |
| `ENVIRONMENT` | ✅ | `development` or `production` |
| `ALGORITHM` | — | `HS256` (default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | — | `30` (default) |

---

### 2 — Web App

```bash
cd web
npm install

cp .env.example .env.local    # fill in Firebase + API URL (see table below)

npm run dev                   # starts on http://localhost:5173
```

#### Available Scripts

```bash
npm run dev       # local dev server with HMR
npm run build     # production bundle → web/dist/
npm run preview   # preview the production build locally
```

#### Web Environment Variables (`web/.env.local`)

| Variable | Example | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | FastAPI base URL |
| `VITE_FIREBASE_API_KEY` | `AIza…` | Firebase Web API key |
| `VITE_FIREBASE_AUTH_DOMAIN` | `project.firebaseapp.com` | Firebase Auth domain |
| `VITE_FIREBASE_PROJECT_ID` | `my-project` | Firebase project ID |
| `VITE_FIREBASE_STORAGE_BUCKET` | `project.appspot.com` | Firebase Storage bucket |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | `123456…` | Firebase Sender ID |
| `VITE_FIREBASE_APP_ID` | `1:123:web:abc` | Firebase Web App ID |

> **Note**: All `VITE_*` variables are **baked into the bundle at build time** by Vite. Set the correct values in your CI/CD environment before running `npm run build` for production.

#### Web Routes

| Path | Page | Auth |
|---|---|---|
| `/login` | Login — Google, email link, guest | Public |
| `/` | Home dashboard | Protected |
| `/history` | Scan history (paginated) | Protected |
| `/profile` | Health profile editor | Protected |
| `/scan` | Manual scan — barcode or paste ingredients | Protected |
| `/results/:id` | Scan results detail | Protected |

---

### 3 — Mobile App (Flutter)

```bash
cd mobile
flutter pub get
flutter run                    # runs on connected device / emulator
```

Configure Firebase by placing your `google-services.json` (Android) and `GoogleService-Info.plist` (iOS) in the standard Flutter locations. See [FlutterFire setup docs](https://firebase.flutter.dev/docs/overview).

---

## API Reference

Base URL: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`  
ReDoc: `http://localhost:8000/redoc`

### Auth

All protected endpoints require:
```
Authorization: Bearer <Firebase_ID_Token>
```

### Endpoints

#### Scan

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/scan/analyse` | Optional | Analyse a list of ingredient strings |
| `POST` | `/scan/barcode` | Optional | Look up product by barcode (Open Food Facts) |

**`POST /scan/analyse`**
```json
// Request
{ "ingredients": ["Water", "Sugar", "E621", "Palm Oil"] }

// Response
{
  "ingredients": [{ "name": "E621", "status": "danger", "reason": "MSG — linked to headaches" }],
  "safety_score": 52,
  "nova_class": 3,
  "breakdown": {
    "allergenDeduction": 0, "novaDeduction": 15,
    "additiveDeduction": 10, "conditionDeduction": 0
  }
}
```

**`POST /scan/barcode`**
```json
// Request
{ "barcode": "3017620422003" }

// Response — same shape as /scan/analyse, plus product_name, brand, nutrients
```

> Authenticated scans are **automatically saved** to history — no separate POST required.

#### History

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/history` | Required | List scans. Query params: `limit` (default 20), `offset` (default 0) |
| `GET` | `/history/{id}` | Required | Get a single scan by ID |

#### User / Profile

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/users/me` | Required | Get current user profile |
| `PATCH` | `/users/me` | Required | Update profile (allergies, conditions, goals, display_name) |

---

## Features

### Personalised health scoring

Each product receives a score from **0–100**, deducted by:

- **Allergen match** — flags if any ingredient matches the user's declared allergens
- **NOVA processing tier** — deduction grows from NOVA 1 (natural) → NOVA 4 (ultra-processed)
- **Additive/E-code flags** — known harmful additives lower the score
- **Health conditions** — e.g. Diabetes amplifies sugar deductions; Hypertension amplifies sodium deductions

Score bands:
| Score | Verdict |
|---|---|
| 75–100 | ✅ Great Choice |
| 50–74 | ⚠️ Consume Moderately |
| 25–49 | 🔴 Poor Nutritional Quality |
| 0–24 | 🚫 Avoid — Very Unhealthy |

### Guest mode (web + mobile)

Users can scan without an account. Scans are local-only — not synced to the backend. Guest state is persisted in `localStorage` (web) and `SharedPreferences` (mobile).

### Barcode lookup

Uses the [Open Food Facts](https://world.openfoodfacts.org/) open database. Supports EAN-8, EAN-13, UPC-A.

---

## Security

- Firebase JWTs are verified server-side using the Firebase Admin SDK on every protected request
- Rate-limited to **30 requests/minute** per IP on scan endpoints (via SlowAPI + Redis)
- Secret key and Firebase credentials are **never committed** — all in `.env` (gitignored)
- See [`backend/.env.example`](./backend/.env.example) for the full variable list

---

## Project Status

| Component | Status |
|---|---|
| Backend API | ✅ Complete |
| Flutter mobile app | ✅ Complete |
| React web app | ✅ Complete — production build verified |
| CI/CD pipeline | 🔧 Planned |
| iOS TestFlight | 🔧 Planned |
