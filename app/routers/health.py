"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/v1/health")
async def health():
    return {"status": "healthy", "version": "0.1.0"}
