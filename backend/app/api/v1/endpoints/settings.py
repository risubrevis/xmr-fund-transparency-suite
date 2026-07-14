from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_api_key
from app.logging import get_logger
from app.schemas import (
    DateTimeFormatResponse,
    DateTimeFormatUpdate,
    LocaleResponse,
    LocaleUpdate,
)
from app.settings import (
    get_datetime_format,
    set_datetime_format,
    get_locale,
    set_locale,
)
from app.validators import validate_datetime_format

logger = get_logger("api.settings")
router = APIRouter()

# Locale codes supported by the frontend i18n bundle
SUPPORTED_LOCALES = {"en", "es", "ptBR", "fr", "de", "uk", "be", "ru"}


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


@router.get("/settings/locale", response_model=LocaleResponse)
async def get_locale_setting() -> LocaleResponse:
    """Get the configured UI locale code.

    Public: the locale is a non-sensitive global UI preference used to render
    the login screen before authentication.
    """
    return LocaleResponse(locale=get_locale())


@router.put("/settings/locale", response_model=LocaleResponse)
async def update_locale_setting(
    body: LocaleUpdate,
    api_key: str = Depends(verify_api_key),
) -> LocaleResponse:
    """Update the UI locale code."""
    locale_code = body.locale.strip()
    if locale_code not in SUPPORTED_LOCALES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported locale. Supported: {', '.join(sorted(SUPPORTED_LOCALES))}",
        )
    saved = set_locale(locale_code)
    logger.info("locale_updated", locale=saved)
    return LocaleResponse(locale=saved)
