from fastapi import APIRouter, HTTPException
import logging
from backend.app.utils.system_diagnostics import get_system_diagnostics

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/diagnostics")
async def get_diagnostics():
    """
    Returns real-time resource utilization (RAM, CPU), Python environment details,
    and Polars optimization flags.
    """
    try:
        diagnostics = get_system_diagnostics()
        return diagnostics
    except Exception as e:
        logger.error(f"Diagnostics retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to gather system diagnostics: {str(e)}"
        )
