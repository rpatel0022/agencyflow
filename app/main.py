import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings

logger = logging.getLogger("agencyflow")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AgencyFlow starting up")
    yield
    logger.info("AgencyFlow shutting down")


app = FastAPI(
    title="AgencyFlow",
    description="Multi-agent AI platform for marketing agency campaign workflows",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Scrub any API keys that might leak in error messages
    message = str(exc)
    if settings.gemini_api_key and settings.gemini_api_key in message:
        message = message.replace(settings.gemini_api_key, "[REDACTED]")
    logger.error(f"Unhandled error: {message}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "version": "0.1.0"}
