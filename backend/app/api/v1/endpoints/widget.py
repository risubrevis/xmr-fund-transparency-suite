import base64
import io
from datetime import datetime, timezone

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Fund, Transaction
from app.settings import get_widget_base_color, get_widget_text_color

router = APIRouter()


def _generate_qr_data_url(data: str, size: int = 200) -> str:
    """Generate a QR code as a base64 PNG data URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#000000", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


WIDGET_JS_TEMPLATE = """
function xmrCopyAddr(btn) {
    var addr = btn.getAttribute('data-addr');
    function done() { btn.textContent = 'Copy Address'; }
    function fallback() {
        var ta = document.createElement('textarea');
        ta.value = addr;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        btn.textContent = 'Copied!';
        setTimeout(done, 2000);
    }
    try {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(addr).then(function() {
                btn.textContent = 'Copied!';
                setTimeout(done, 2000);
            }).catch(fallback);
        } else {
            fallback();
        }
    } catch(e) {
        fallback();
    }
}

(function() {
    var container = document.getElementById('xmr-fund-widget');
    if (!container) return;

    function hexToHsl(hex) {
        var r = parseInt(hex.slice(1, 3), 16) / 255;
        var g = parseInt(hex.slice(3, 5), 16) / 255;
        var b = parseInt(hex.slice(5, 7), 16) / 255;
        var max = Math.max(r, g, b), min = Math.min(r, g, b);
        var h, s, l = (max + min) / 2;
        if (max === min) { h = s = 0; } else {
            var d = max - min;
            s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
            if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
            else if (max === g) h = ((b - r) / d + 2) / 6;
            else h = ((r - g) / d + 4) / 6;
        }
        return [h * 360, s * 100, l * 100];
    }

    function hslToHex(h, s, l) {
        h = ((h % 360) + 360) % 360;
        s /= 100; l /= 100;
        var c = (1 - Math.abs(2 * l - 1)) * s;
        var x = c * (1 - Math.abs((h / 60) % 2 - 1));
        var m = l - c / 2;
        var r, g, b;
        if (h < 60) { r = c; g = x; b = 0; }
        else if (h < 120) { r = x; g = c; b = 0; }
        else if (h < 180) { r = 0; g = c; b = x; }
        else if (h < 240) { r = 0; g = x; b = c; }
        else if (h < 300) { r = x; g = 0; b = c; }
        else { r = c; g = 0; b = x; }
        var rs = Math.round((r + m) * 255).toString(16).padStart(2, '0');
        var gs = Math.round((g + m) * 255).toString(16).padStart(2, '0');
        var bs = Math.round((b + m) * 255).toString(16).padStart(2, '0');
        return '#' + rs + gs + bs;
    }

    function shiftHue(hex, degrees) {
        var hsl = hexToHsl(hex);
        return hslToHex(hsl[0] + degrees, hsl[1], hsl[2]);
    }

    fetch('APP_ORIGIN_PLACEHOLDER/widget/UUID_PLACEHOLDER.json')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var baseColor = data.base_color || '#667eea';
            var textColor = data.text_color || '#ffffff';
            var endColor = shiftHue(baseColor, 40);
            var trackColor = 'rgba(' +
                parseInt(textColor.slice(1, 3), 16) + ',' +
                parseInt(textColor.slice(3, 5), 16) + ',' +
                parseInt(textColor.slice(5, 7), 16) + ',0.3)';
            var progressHtml = '';
            if (data.target_amount_xmr) {
                var pct = Math.min(
                    (parseFloat(data.total_received_xmr) / parseFloat(data.target_amount_xmr)) * 100,
                    100
                );
                progressHtml =
                    '<div style="margin-top:12px;">' +
                    '<div style="background:' + trackColor + ';border-radius:8px;overflow:hidden;height:8px;">' +
                    '<div style="background:' + textColor + ';height:8px;width:' + pct.toFixed(1) + '%;"></div>' +
                    '</div>' +
                    '<div style="font-size:12px;opacity:0.9;margin-top:4px;">' +
                    data.total_received_xmr + ' / ' + data.target_amount_xmr + ' XMR' +
                    '</div></div>';
            }
            var addrShort = data.deposit_address.slice(0, 10) + '...' + data.deposit_address.slice(-10);
            var rightHtml =
                '<div style="display:flex;flex-direction:column;align-items:center;min-width:140px;">' +
                '<img src="' + data.qr_code + '" alt="QR Code" style="width:140px;height:140px;border-radius:8px;background:#fff;padding:4px;" />' +
                '<div style="font-size:10px;opacity:0.7;word-break:break-all;margin-top:8px;text-align:center;">' +
                addrShort + '</div>' +
                '<button data-addr="' + data.deposit_address + '" onclick="xmrCopyAddr(this)" ' +
                'style="margin-top:6px;font-size:11px;padding:4px 10px;border-radius:6px;border:1px solid ' + textColor + ';background:transparent;color:' + textColor + ';cursor:pointer;opacity:0.9;">Copy Address</button>' +
                '</div>';
            container.innerHTML = '<div style="' +
                'font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;' +
                'background: linear-gradient(135deg, ' + baseColor + ' 0%, ' + endColor + ' 100%);' +
                'color: ' + textColor + '; padding: 24px; border-radius: 12px;' +
                'box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 600px;' +
                'display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap;">' +
                '<div style="flex:1;min-width:200px;">' +
                '<div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">' +
                '&#128176; ' + data.label + '</div>' +
                (data.description ? '<div style="font-size: 12px; opacity: 0.8; margin-bottom: 6px;">' + data.description + '</div>' : '') +
                '<div style="font-size: 36px; font-weight: bold; margin-bottom: 8px;">' +
                data.total_received_xmr + ' XMR</div>' +
                progressHtml +
                '<div style="font-size: 12px; opacity: 0.8; margin-top: 8px;">' +
                'Updated: ' + data.last_updated + '</div>' +
                '</div>' +
                rightHtml +
                '</div>';
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

    widget_js = WIDGET_JS_TEMPLATE.replace("UUID_PLACEHOLDER", uuid).replace(
        "APP_ORIGIN_PLACEHOLDER", settings.app_origin
    )

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

    deposit_addr = fund.deposit_address or fund.primary_address

    # Monero URI scheme: monero:<address> — recognized by wallet apps
    qr_data_url = _generate_qr_data_url(f"monero:{deposit_addr}")

    data = {
        "label": fund.label,
        "description": fund.description or "",
        "deposit_address": deposit_addr,
        "qr_code": qr_data_url,
        "total_received_xmr": f"{total_xmr:.2f}",
        "target_amount_xmr": f"{fund.target_amount_xmr:.2f}"
        if fund.target_amount_xmr is not None
        else None,
        "transaction_count": tx_count,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "base_color": get_widget_base_color(),
        "text_color": get_widget_text_color(),
    }

    return JSONResponse(
        content=data,
        headers={
            "Cache-Control": "public, max-age=60",
            "Access-Control-Allow-Origin": "*",
        },
    )
