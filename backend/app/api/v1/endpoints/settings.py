from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_api_key
from app.logging import get_logger
from app.schemas import (
    DateTimeFormatResponse,
    DateTimeFormatUpdate,
)
from app.settings import (
    get_datetime_format,
    set_datetime_format,
)
from app.validators import validate_datetime_format

logger = get_logger("api.settings")
router = APIRouter()


@router.get("/settings/datetime-format", response_model=DateTimeFormatResponse)
async def get_datetime_format_setting(
    api_key: str = Depends(verify_api_key),
) -> DateTimeFormatResponse:
    """Get the current datetime format pattern."""
    pattern = get_datetime_format()
    return DateTimeFormatResponse(pattern=pattern)


@router.put("/settings/datetime-format", response_model=DateTimeFormatResponse)
async def update_datetime_format_setting(
    body: DateTimeFormatUpdate,
    api_key: str = Depends(verify_api_key),
) -> DateTimeFormatResponse:
    """Update the datetime format pattern."""
    # Validate and strip the format
    is_valid, error_msg = validate_datetime_format(body.pattern)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Use the stripped value (validator already strips but we ensure it here too)
    stripped_pattern = body.pattern.strip()
    pattern = set_datetime_format(stripped_pattern)
    logger.info("datetime_format_updated", pattern=pattern)
    return DateTimeFormatResponse(pattern=pattern)
