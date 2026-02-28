import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.gemini_client import GeminiClient
from app.routers.health import router as health_router
from app.routers.pipeline import router as pipeline_router
from app.services.pipeline_orchestrator import PipelineOrchestrator

logger = logging.getLogger("agencyflow")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create shared resources on startup, clean up on shutdown.

    WHY lifespan over @app.on_event: lifespan is the modern FastAPI pattern.
    It uses a context manager so startup and shutdown are in one place, and
    the resources (like GeminiClient) are guaranteed to be cleaned up.
    """
    logger.info("AgencyFlow starting up")
    # Create the Gemini client and pipeline orchestrator once, shared across requests
    client = GeminiClient()
    app.state.orchestrator = PipelineOrchestrator(client)
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


app.include_router(health_router)
app.include_router(pipeline_router)
