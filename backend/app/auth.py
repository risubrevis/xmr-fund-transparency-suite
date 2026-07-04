from fastapi import Header, HTTPException, Query

from app.config import settings


async def verify_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    api_key: str | None = Query(None, alias="api_key"),
) -> str:
    """Verify the API key from request header or query parameter.

    Header takes precedence over query parameter.
    """
    key = x_api_key or api_key
    if not key:
        raise HTTPException(status_code=401, detail="API key required")
    if key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key
