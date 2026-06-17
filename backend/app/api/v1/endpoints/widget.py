from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Fund, Transaction

router = APIRouter()

WIDGET_JS_TEMPLATE = """
(function() {
    var container = document.getElementById('xmr-fund-widget');
    if (!container) return;

    fetch('/widget/UUID_PLACEHOLDER.json')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            container.innerHTML = '<div style="' +
                'font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;' +
                'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);' +
                'color: white; padding: 24px; border-radius: 12px;' +
                'box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 400px;">' +
                '<div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">' +
                '&#128176; ' + data.label + '</div>' +
                '<div style="font-size: 36px; font-weight: bold; margin-bottom: 8px;">' +
                data.total_received_xmr + ' XMR</div>' +
                '<div style="font-size: 12px; opacity: 0.8;">' +
                'Updated: ' + data.last_updated + '</div></div>';
        })
        .catch(function(err) {
            container.innerHTML = '<div style="color: red;">Failed to load widget</div>';
        });
})();
"""


@router.get("/widget/{uuid}.js")
async def get_widget_js(
    uuid: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Return JS widget script for embedding."""
    result = await db.execute(select(Fund).where(Fund.public_uuid == uuid))
    fund = result.scalar_one_or_none()

    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    widget_js = WIDGET_JS_TEMPLATE.replace("UUID_PLACEHOLDER", uuid)

    return Response(
        content=widget_js,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/widget/{uuid}.json")
async def get_widget_json(
    uuid: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Return widget data as JSON."""
    result = await db.execute(select(Fund).where(Fund.public_uuid == uuid))
    fund = result.scalar_one_or_none()

    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    total_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount_xmr), 0)).where(
            Transaction.fund_id == fund.id
        )
    )
    total_xmr = total_result.scalar()

    tx_count_result = await db.execute(
        select(func.count(Transaction.id)).where(Transaction.fund_id == fund.id)
    )
    tx_count = tx_count_result.scalar()

    data = {
        "label": fund.label,
        "total_received_xmr": f"{total_xmr:.2f}",
        "transaction_count": tx_count,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    return JSONResponse(
        content=data,
        headers={
            "Cache-Control": "public, max-age=60",
            "Access-Control-Allow-Origin": "*",
        },
    )
