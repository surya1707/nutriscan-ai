# NutriScan AI Backend

This is the backend service for NutriScan AI.

## Local Setup

### Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in the required values for your local environment.

### Generating a SECRET_KEY

For local development, you need a strong `SECRET_KEY`. You can generate one using Python:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Place the generated string in your `.env` file as the `SECRET_KEY` value.

## Environment Variables Reference

| Variable | Description |
| -------- | ----------- |
| `PROJECT_NAME` | The name of the project (default: NutriScan AI Backend). |
| `DATABASE_URL` | The SQLAlchemy connection string for the database. |
| `REDIS_URL` | The connection string for the Redis instance used for caching/queues. |
| `SECRET_KEY` | A strong, random cryptographic key used for signing JWT tokens and other security features. |
| `ALGORITHM` | The algorithm used for JWT token encoding (e.g., HS256). |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | The duration in minutes for which an access token remains valid. |
| `ENVIRONMENT` | The application environment (e.g., development, staging, production). |
| `FIREBASE_PROJECT_ID` | The ID of your Firebase project. |
| `FIREBASE_CREDENTIALS_PATH` | The local path to your Firebase service account JSON credentials file. |

### Firebase Credentials

To use Firebase authentication, you must download a service account key:
1. Go to the Firebase console for the existing NutriScan project.
2. Navigate to **Project settings > Service accounts**.
3. Click **Generate new private key** and save the JSON file locally.
4. Set `FIREBASE_CREDENTIALS_PATH` in your `.env` to the absolute or relative path of that JSON file.

## Running with Docker Compose

To start the backend and its dependencies (like PostgreSQL and Redis) using Docker Compose, run:

```bash
docker-compose up --build
```

This will spin up the database, Redis, and the FastAPI application.
