from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_api_key
from app.logging import get_logger
from app.schemas import (
    DateTimeFormatResponse,
    DateTimeFormatUpdate,
    WidgetColorResponse,
    WidgetColorUpdate,
    WidgetTextColorResponse,
    WidgetTextColorUpdate,
)
from app.settings import (
    get_datetime_format,
    get_widget_base_color,
    get_widget_text_color,
    set_datetime_format,
    set_widget_base_color,
    set_widget_text_color,
)
from app.validators import validate_datetime_format, validate_hex_color

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


@router.get("/settings/widget-color", response_model=WidgetColorResponse)
async def get_widget_color_setting(
    api_key: str = Depends(verify_api_key),
) -> WidgetColorResponse:
    """Get the current widget base color."""
    color = get_widget_base_color()
    return WidgetColorResponse(color=color)


@router.put("/settings/widget-color", response_model=WidgetColorResponse)
async def update_widget_color_setting(
    body: WidgetColorUpdate,
    api_key: str = Depends(verify_api_key),
) -> WidgetColorResponse:
    """Update the widget base color."""
    is_valid, error_msg = validate_hex_color(body.color)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    stripped_color = body.color.strip()
    color = set_widget_base_color(stripped_color)
    logger.info("widget_color_updated", color=color)
    return WidgetColorResponse(color=color)


@router.get("/settings/widget-text-color", response_model=WidgetTextColorResponse)
async def get_widget_text_color_setting(
    api_key: str = Depends(verify_api_key),
) -> WidgetTextColorResponse:
    """Get the current widget text color."""
    color = get_widget_text_color()
    return WidgetTextColorResponse(color=color)


@router.put("/settings/widget-text-color", response_model=WidgetTextColorResponse)
async def update_widget_text_color_setting(
    body: WidgetTextColorUpdate,
    api_key: str = Depends(verify_api_key),
) -> WidgetTextColorResponse:
    """Update the widget text color."""
    is_valid, error_msg = validate_hex_color(body.color)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    stripped_color = body.color.strip()
    color = set_widget_text_color(stripped_color)
    logger.info("widget_text_color_updated", color=color)
    return WidgetTextColorResponse(color=color)
