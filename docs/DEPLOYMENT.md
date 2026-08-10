# NutriScan AI — Deployment Guide

This document covers everything you need to get NutriScan AI running — from your local machine during development to a full production deployment in the cloud.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Prerequisites](#2-prerequisites)
3. [Firebase Setup (Required for Both Environments)](#3-firebase-setup)
4. [Local Development](#4-local-development)
   - [4a. Backend (Without Docker)](#4a-backend-without-docker)
   - [4b. Backend (With Docker)](#4b-backend-with-docker)
   - [4c. Web Frontend](#4c-web-frontend)
5. [Production Deployment — Backend (Render)](#5-production-deployment--backend-render)
6. [Production Deployment — Web Frontend (Vercel / Netlify)](#6-production-deployment--web-frontend)
7. [Environment Variable Reference](#7-environment-variable-reference)
8. [Post-Deployment Health Check](#8-post-deployment-health-check)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Project Overview

NutriScan AI is a monorepo with three main components:

| Directory  | Purpose                                      | Stack                         |
|------------|----------------------------------------------|-------------------------------|
| `backend/` | REST API & business logic                    | FastAPI · SQLAlchemy · Alembic|
| `web/`     | Browser-based companion app                  | React · Vite · TypeScript     |
| `mobile/`  | Cross-platform mobile app                    | Flutter                       |

The backend requires a **PostgreSQL** database, a **Redis** cache, and a **Firebase** service account (for verifying user identity tokens). The web frontend requires only the Firebase Web SDK keys and the backend API URL.

---

## 2. Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org/) |
| Git | any | [git-scm.com](https://git-scm.com/) |
| Docker Desktop *(optional)* | any | [docker.com](https://www.docker.com/products/docker-desktop/) |

> **Note:** Docker is only needed for the Docker-based local setup. You can run the backend natively with Python and SQLite without any Docker setup.

---

## 3. Firebase Setup

Firebase powers authentication across both the mobile app and the web frontend.

### 3.1 Create a Firebase Project

1. Go to the [Firebase Console](https://console.firebase.google.com/) and sign in with a Google account.
2. Click **Add project**, enter a project name (e.g., `nutriscan1`), and complete the setup wizard.
3. In the left sidebar, go to **Authentication → Get started** and enable the **Google** sign-in provider (and/or Email/Password if needed).

### 3.2 Get the Firebase Project ID

1. Click the ⚙️ gear icon (top-left) → **Project settings**.
2. Under the **General** tab, copy the **Project ID** (e.g., `nutriscan1-07ab`).
3. This value is your `FIREBASE_PROJECT_ID`.

### 3.3 Generate a Service Account Key (Backend)

1. In **Project settings**, click the **Service accounts** tab.
2. Select **Firebase Admin SDK** and click **Generate new private key**.
3. A `.json` file will download. **Keep this secret — never commit it to Git.**
4. Move the file into the `backend/` folder (e.g., rename it `firebase-credentials.json`).
5. Add `firebase-credentials.json` to your `.gitignore`.

### 3.4 Get Web SDK Config (Web Frontend)

1. In **Project settings → Your apps**, click **Add app** → select the **Web** (`</>`) icon.
2. Register the app (no hosting needed), then copy the `firebaseConfig` object values.
3. These values map to the `VITE_FIREBASE_*` environment variables in the web `.env.local` file.

---

## 4. Local Development

### 4a. Backend (Without Docker)

This is the fastest way to get started — uses **SQLite** (no database server needed) and skips Redis gracefully.

```powershell
# 1. Enter the backend directory
cd backend

# 2. Copy the example .env file
cp .env.example .env

# 3. Edit .env:
#    - Set FIREBASE_PROJECT_ID to your Firebase Project ID
#    - Set FIREBASE_CREDENTIALS_PATH to ./firebase-credentials.json
#    - Leave DATABASE_URL as sqlite+aiosqlite:///./nutriscan.db (default)
#    - Set a strong SECRET_KEY

# 4. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # macOS / Linux

# 5. Install dependencies
pip install -r requirements.txt

# 6. Run database migrations (creates tables in nutriscan.db)
alembic upgrade head

# 7. Start the development server
uvicorn app.main:app --reload
```

The API will be available at **`http://127.0.0.1:8000`**.  
Interactive API docs: **`http://127.0.0.1:8000/docs`**.

---

### 4b. Backend (With Docker)

Requires Docker Desktop to be running.

```powershell
cd backend

# Copy and configure .env
cp .env.example .env
# Edit .env: uncomment the PostgreSQL DATABASE_URL line and comment out the SQLite one

# Build and start all services (API + PostgreSQL + Redis)
docker compose up --build
```

> **Tip:** The `DATABASE_URL` for Docker should be:
> `postgresql+asyncpg://nutriuser:nutripass@db:5432/nutriscan`

---

### 4c. Web Frontend

```powershell
cd web

# 1. Copy the example .env file
cp .env.example .env.local

# 2. Edit .env.local:
#    - Set VITE_API_URL=http://localhost:8000
#    - Fill in all VITE_FIREBASE_* values from your Firebase Web SDK config

# 3. Install dependencies
npm install

# 4. Start the development server
npm run dev
```

The web app will be available at **`http://localhost:5173`**.

---

## 5. Production Deployment — Backend (Render)

[Render](https://render.com/) is a simple PaaS that can build and host the Dockerised backend, with managed PostgreSQL and Redis available on the free tier.

### Step 1 — Create the PostgreSQL Database

1. In the Render Dashboard, click **New +** → **PostgreSQL**.
2. Name it (e.g., `nutriscan-db`), choose your nearest region, and click **Create Database**.
3. After creation, copy the **Internal Database URL** from the dashboard.

> **Important:** Render gives you a URL starting with `postgres://`. You **must** change the scheme to `postgresql+asyncpg://` before pasting it into your backend environment variables.

### Step 2 — Create the Redis Instance

1. In the Render Dashboard, click **New +** → **Redis**.
2. Name it (e.g., `nutriscan-redis`), choose the same region, and click **Create Redis**.
3. After creation, copy the **Internal Redis URL** (starts with `redis://`).

### Step 3 — Deploy the Backend Web Service

1. Click **New +** → **Web Service** and connect your GitHub/GitLab repo.
2. Set the **Root Directory** to `backend`.
3. Set **Environment** to `Docker`.
4. Set the **Start Command** to:
   ```bash
   sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 10000"
   ```
   *(Render routes traffic to port 10000 by default.)*

5. Under **Environment Variables**, add:

| Key | Value |
|-----|-------|
| `PROJECT_NAME` | `NutriScan AI Backend` |
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | Your Internal Database URL (with `postgresql+asyncpg://` scheme) |
| `REDIS_URL` | Your Internal Redis URL |
| `SECRET_KEY` | A strong random string — generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
| `FIREBASE_PROJECT_ID` | Your Firebase Project ID |
| `FIREBASE_CREDENTIALS_PATH` | `/etc/secrets/firebase-credentials.json` |
| `ALLOWED_ORIGINS` | Your frontend URL(s), comma-separated (e.g., `https://nutriscan.vercel.app`) |

6. Under **Secret Files**, click **Add Secret File**:
   - **Filename:** `/etc/secrets/firebase-credentials.json`
   - **Contents:** Paste the full JSON content of your Firebase service account key file.

7. Click **Create Web Service**. Render will build and deploy automatically.

Your API will be live at a URL like `https://nutriscan-api.onrender.com`.

---

## 6. Production Deployment — Web Frontend

### Option A: Vercel (Recommended)

1. Push your repository to GitHub.
2. Go to [vercel.com](https://vercel.com/) and import your GitHub repository.
3. Set the **Root Directory** to `web`.
4. Vercel will auto-detect the Vite framework.
5. Under **Environment Variables**, add all `VITE_*` variables:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://nutriscan-api.onrender.com` (your Render backend URL) |
| `VITE_FIREBASE_API_KEY` | From Firebase Web SDK config |
| `VITE_FIREBASE_AUTH_DOMAIN` | From Firebase Web SDK config |
| `VITE_FIREBASE_PROJECT_ID` | From Firebase Web SDK config |
| `VITE_FIREBASE_STORAGE_BUCKET` | From Firebase Web SDK config |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | From Firebase Web SDK config |
| `VITE_FIREBASE_APP_ID` | From Firebase Web SDK config |

6. Click **Deploy**.

### Option B: Netlify

1. Go to [app.netlify.com](https://app.netlify.com/) → **Add new site → Import an existing project**.
2. Connect your GitHub repo and set **Base directory** to `web`.
3. Set **Build command** to `npm run build`.
4. Set **Publish directory** to `web/dist`.
5. Add the same `VITE_*` environment variables as listed above.
6. Click **Deploy site**.

> **Important:** After deployment, go to your Firebase Console → **Authentication → Settings → Authorized domains** and add your new Vercel/Netlify domain (e.g., `nutriscan.vercel.app`). Without this, Firebase sign-in will be blocked.

---

## 7. Environment Variable Reference

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PROJECT_NAME` | No | `NutriScan AI Backend` | Display name in API docs |
| `DATABASE_URL` | **Yes** | — | Full SQLAlchemy DB URL. Use `sqlite+aiosqlite:///./nutriscan.db` for local dev, `postgresql+asyncpg://...` for prod |
| `REDIS_URL` | **Yes** | — | Redis connection URL. Errors are non-fatal in dev |
| `SECRET_KEY` | **Yes** | — | JWT signing secret. Must be a long, random string in production |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | JWT token lifetime in minutes |
| `ENVIRONMENT` | No | `development` | Set to `production` in prod |
| `ALLOWED_ORIGINS` | No | `http://localhost,...` | Comma-separated list of allowed CORS origins |
| `FIREBASE_PROJECT_ID` | No | — | Firebase project ID. Needed for Firebase Auth token verification |
| `FIREBASE_CREDENTIALS_PATH` | No | — | Path to the Firebase service account JSON key file |

### Web Frontend (`web/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | **Yes** | Base URL of the backend API (no trailing slash) |
| `VITE_FIREBASE_API_KEY` | **Yes** | Firebase Web SDK API key |
| `VITE_FIREBASE_AUTH_DOMAIN` | **Yes** | Firebase auth domain (e.g., `your-project.firebaseapp.com`) |
| `VITE_FIREBASE_PROJECT_ID` | **Yes** | Firebase project ID |
| `VITE_FIREBASE_STORAGE_BUCKET` | **Yes** | Firebase storage bucket |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | **Yes** | Firebase messaging sender ID |
| `VITE_FIREBASE_APP_ID` | **Yes** | Firebase app ID |

---

## 8. Post-Deployment Health Check

Once both services are deployed, verify everything is working:

```bash
# 1. Check the backend health endpoint
curl https://nutriscan-api.onrender.com/health

# Expected response:
# {"status":"ok","db":"ok","redis":"ok","environment":"production"}

# 2. Check the API docs are accessible
# Visit: https://nutriscan-api.onrender.com/docs

# 3. Open the web app and try signing in
# Visit: https://your-app.vercel.app
```

A healthy `/health` response confirms:
- The API server is running
- The database connection is live
- The Redis cache connection is live

---

## 9. Troubleshooting

### `open //./pipe/dockerDesktopLinuxEngine` error
Docker Desktop is not running. Launch Docker Desktop and wait for it to fully initialize (green indicator in the system tray) before running `docker compose up`.

### `alembic.util.exc.CommandError: Can't locate revision`
Your migration history is out of sync. Run:
```bash
alembic stamp head
alembic upgrade head
```

### Firebase Admin initialization error
- Ensure `FIREBASE_CREDENTIALS_PATH` points to a valid file that exists at that exact path.
- On Render, verify the Secret File was saved with filename `/etc/secrets/firebase-credentials.json` and the contents are valid JSON.

### CORS errors in the browser
- Ensure `ALLOWED_ORIGINS` in the backend `.env` includes the exact URL of your deployed frontend (no trailing slash, no wildcard in production).
- In Firebase Console, ensure your frontend domain is listed under **Authentication → Settings → Authorized domains**.

### `422 Unprocessable Entity` from the API
The request body format doesn't match what the endpoint expects. Check the request against the API docs at `/docs` and ensure `Content-Type: application/json` is being sent.

### Render service is slow to respond (free tier)
Render's free tier spins down services after 15 minutes of inactivity. The first request after a cold start may take 30–60 seconds. Consider upgrading to a paid tier or using an uptime monitoring service (e.g., [UptimeRobot](https://uptimerobot.com/)) to ping `/health` every 10 minutes and keep the service warm.
