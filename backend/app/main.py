import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.api.routes import chat, documents, onboarding, pipeline, playbook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting LexOnboard API — environment: {settings.ENVIRONMENT}")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified.")
    yield
    logger.info("Shutting down LexOnboard API.")


app = FastAPI(
    title="LexOnboard API",
    description="AI-powered legal contract onboarding platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://lexonboard.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(playbook.router, prefix="/api")
app.include_router(onboarding.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}