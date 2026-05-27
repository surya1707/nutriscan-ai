from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import scan
from .core.config import settings
from .core.database import engine, Base
from .models import user, history # Import models for discovery

app = FastAPI(title=settings.PROJECT_NAME)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router)

@app.get("/")
async def root():
    return {"message": "Welcome to NutriScan AI API", "status": "online"}
