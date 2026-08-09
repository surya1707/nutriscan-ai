# Deploying NutriScan AI Backend

This guide outlines how to deploy the NutriScan AI backend to a production environment using **Render**, a popular and developer-friendly PaaS. Render can natively host our Dockerized application alongside a managed PostgreSQL database and a Redis instance.

## Prerequisites

1. A [Render account](https://render.com/).
2. Your repository pushed to GitHub or GitLab.

## 1. Set up the Managed PostgreSQL Database

1. In the Render Dashboard, click **New +** and select **PostgreSQL**.
2. Name it (e.g., `nutriscan-db`).
3. Choose the region closest to your users.
4. Select the Free or Starter tier.
5. Click **Create Database**.
6. Once created, copy the **Internal Database URL** (e.g., `postgresql://...`). You will need this for the backend service.

## 2. Set up the Redis Instance

1. In the Render Dashboard, click **New +** and select **Redis**.
2. Name it (e.g., `nutriscan-redis`).
3. Choose the same region as your database.
4. Select the Free tier.
5. Click **Create Redis**.
6. Once created, copy the **Internal Redis URL** (e.g., `redis://...`). You will need this for the backend service.

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
| `DATABASE_URL` | *(Paste Internal Database URL)* | Must start with `postgresql+asyncpg://...` (Render gives you `postgres://...`, so **change `postgres://` to `postgresql+asyncpg://`**) |
| `REDIS_URL` | *(Paste Internal Redis URL)* | e.g. `redis://red-xxx:6379` |
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

- You can hit the `https://nutriscan-api.onrender.com/health` endpoint to ensure the DB and Redis are connected successfully.
- All request logs and unhandled exceptions (with full stack traces) will now stream directly to your Render Logs tab, while returning clean JSON errors to your app.
