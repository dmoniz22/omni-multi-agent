"""Health check endpoints."""

from fastapi import APIRouter

from omni.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("")
async def health_check() -> dict:
    """Basic health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy", "service": "omni-api"}


@router.get("/ready")
async def readiness_check() -> dict:
    """Readiness check endpoint.

    Returns:
        Ready status
    """
    return {"ready": True}


@router.get("/live")
async def liveness_check() -> dict:
    """Liveness check endpoint.

    Returns:
        Live status
    """
    return {"alive": True}
