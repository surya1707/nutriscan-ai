# Deploying NutriScan AI Backend

This guide outlines how to deploy the NutriScan AI backend to a production environment using **Render** (for hosting the API and key-value cache) and **Neon.tech** (for the managed serverless PostgreSQL database).

## Prerequisites

1. A [Render account](https://render.com/).
2. Your repository pushed to GitHub or GitLab.

## 1. Set up the PostgreSQL Database (Neon.tech)

> Neon offers a generous free tier with serverless Postgres and a built-in connection pooler.

1. Go to [neon.tech](https://neon.tech/) and sign in (or create a free account).
2. Click **New Project**, name it (e.g., `nutriscan`), and choose your nearest region.
3. In the **Connection Details** panel, click the **Pooled connection** tab.
4. Copy the connection string — it looks like:
   ```
   postgres://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
   ```
5. **Change the scheme** to `postgresql+asyncpg://` before using it as `DATABASE_URL`:
   ```
   postgresql+asyncpg://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
   ```

> **Important:** Always use the **pooled** connection string to avoid exhausting Neon's connection limits on the free tier.

## 2. Set up the Key Value (Redis) Instance on Render

> Render no longer offers a standalone Redis service. Use the **Key Value** service instead — it is fully Redis-compatible.

1. In the Render Dashboard, click **New +** and select **Key Value**.
2. Name it (e.g., `nutriscan-kv`).
3. Choose the **same region** as your Web Service.
4. Click **Create Key Value**.
5. Once created, open the Key Value's **Info** page and copy the **Internal Redis URL** (starts with `redis://`). You will use this as `REDIS_URL`.

## 3. Deploy the Backend Web Service

1. In the Render Dashboard, click **New +** and select **Web Service**.
2. Connect your GitHub/GitLab repository.
3. Name your service (e.g., `nutriscan-api`).
4. Set the **Root Directory** to `backend` (if you are deploying from a monorepo, otherwise leave blank if `backend` is the root of your repo).
5. Ensure the **Environment** is set to `Docker`.
6. Select your instance type (Free/Starter).
7. Under **Advanced**, add the following **Environment Variables**:

| Key | Value | Notes |
| --- | ----- | ----- |
| `PROJECT_NAME` | `NutriScan AI Backend` | Or your preferred name |
| `ENVIRONMENT` | `production` | Turns off SQLAlchemy echo and enables prod defaults |
| `DATABASE_URL` | *(Paste Neon pooled connection string)* | Must start with `postgresql+asyncpg://...` and include `?sslmode=require`. Neon gives `postgres://...` — change the scheme accordingly |
| `REDIS_URL` | *(Paste Internal Redis URL from Render Key Value)* | e.g. `redis://red-xxx:6379` |
| `SECRET_KEY` | *(A strong random string)* | Use `python -c "import secrets; print(secrets.token_urlsafe(32))"` locally to generate one |
| `ALGORITHM` | `HS256` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Or your preferred duration |
| `ALLOWED_ORIGINS` | `https://your-frontend.com` | Comma-separated list of allowed origins. **Do not use `*` in production.** |

*(Note: For Firebase credentials in production, Render supports "Secret Files" where you can upload your `credentials.json` and set `FIREBASE_CREDENTIALS_PATH` to its path. Or you can use Firebase Admin SDK initialized from env vars directly if you modify the code to support it).*

8. Click **Create Web Service**.

Render will now build your Docker container. Because we configured our `docker-compose.yml` to run `alembic upgrade head` before starting, you must ensure that your Render start command is configured to run migrations, or you can add a script to `Dockerfile` to do this. However, since Render runs the image directly (not `docker-compose.yml`), you should update the **Start Command** in Render settings to:

```bash
sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 10000"
```
*(Render uses port 10000 by default).*

## 4. Update the Flutter App

Once the backend is live, Render will give you a public URL (e.g., `https://nutriscan-api.onrender.com`).

1. Open your Flutter app code.
2. Locate the file where `API_URL` is defined (likely in `lib/core/config/app_config.dart` or a `.env` file).
3. Change it from the hardcoded local IP to your new Render URL:
   ```dart
   const String API_URL = "https://nutriscan-api.onrender.com";
   ```
4. Rebuild and test your app!

## Monitoring

- You can hit the `https://nutriscan-api.onrender.com/health` endpoint to ensure the DB (Neon.tech) and Redis cache (Render Key Value) are connected successfully.
- All request logs and unhandled exceptions (with full stack traces) will now stream directly to your Render Logs tab, while returning clean JSON errors to your app.
