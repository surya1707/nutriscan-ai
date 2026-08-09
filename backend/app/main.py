import time
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from .routers import scan
from .routers import user as user_router
from .routers import history as history_router
from .core.config import settings
from .core.rate_limit import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .core.database import engine, Base
from .models import user, history # Import models for discovery
from .core.cache import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="The core backend service for NutriScan AI. It powers barcode scanning via Open Food Facts, analyzes ingredients against user allergies and health conditions, calculates personalized health scores, and stores cross-device scan histories securely via Firebase Auth.",
    version="1.0.0",
    contact={
        "name": "NutriScan Support",
        "email": "support@nutriscan.ai",
    }
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred."}
    )

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router)
app.include_router(user_router.router)
app.include_router(history_router.router)

@app.get("/")
async def root():
    return {"message": "Welcome to NutriScan AI API", "status": "online"}

@app.get("/health")
async def health_check():
    db_status = "ok"
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    redis_status = "ok"
    try:
        client = await cache.get_client()
        await client.ping()
    except Exception as e:
        redis_status = f"error: {str(e)}"
        
    return {
        "status": "ok" if db_status == "ok" and redis_status == "ok" else "degraded",
        "db": db_status,
        "redis": redis_status,
        "environment": settings.ENVIRONMENT
    }
