import base64
import io
from datetime import datetime, timedelta, timezone
from typing import List

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.filters import (
    SortRule,
    build_date_filter,
    build_order_by,
    build_tier_filter,
    describe_filters,
    parse_sort,
)
from app.models import Fund, Post, Transaction
from app.reports.csv_export import generate_csv_export
from app.reports.json_export import generate_json_export
from app.reports.xml import generate_xml_report
from app.settings import (
    get_datetime_format,
    get_widget_base_color,
    get_widget_text_color,
)

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

var xmrNewsOffset = 0;
var xmrNewsHasPosts = false;
var xmrNewsUuid = '';

function xmrEscapeHtml(text) {
    var d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}

function xmrToggleNews() {
    var content = document.getElementById('xmr-news-content');
    var arrow = document.getElementById('xmr-news-arrow');
    if (!content || !arrow) return;
    if (content.style.display === 'none') {
        content.style.display = 'block';
        arrow.textContent = '\u25b2';
        // Reset and re-fetch on every expand
        xmrNewsOffset = 0;
        xmrFetchNews();
    } else {
        content.style.display = 'none';
        arrow.textContent = '\u25bc';
        // Reset state on collapse
        var postsContainer = document.getElementById('xmr-news-posts');
        if (postsContainer) postsContainer.innerHTML = '';
        var moreBtn = document.getElementById('xmr-news-more');
        if (moreBtn) moreBtn.style.display = 'none';
    }
}

function xmrFetchNews() {
    var container = document.getElementById('xmr-news-posts');
    if (xmrNewsOffset === 0) {
        container.innerHTML = '<div style="text-align:center;padding:8px;opacity:0.7;">Loading...</div>';
    }
    var btn = document.getElementById('xmr-news-more');
    fetch('APP_ORIGIN_PLACEHOLDER/widget/' + xmrNewsUuid + '/posts.json?limit=5&offset=' + xmrNewsOffset)
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (xmrNewsOffset === 0) {
                container.innerHTML = '';
            }
            if (data.posts.length === 0 && xmrNewsOffset === 0) {
                var empty = document.createElement('div');
                empty.style.cssText = 'text-align:center;padding:8px;opacity:0.6;font-size:12px;';
                empty.textContent = 'No news yet';
                container.appendChild(empty);
            }
            data.posts.forEach(function(post) {
                var card = document.createElement('div');
                card.style.cssText = 'background:rgba(255,255,255,0.12);border-radius:8px;padding:10px 12px;margin-bottom:8px;';
                var dateEl = document.createElement('div');
                dateEl.style.cssText = 'font-size:10px;opacity:0.6;margin-bottom:4px;';
                dateEl.textContent = post.created_at;
                var bodyEl = document.createElement('div');
                bodyEl.style.cssText = 'font-size:12px;line-height:1.5;white-space:pre-wrap;word-break:break-word;';
                bodyEl.textContent = post.body;
                card.appendChild(dateEl);
                card.appendChild(bodyEl);
                container.appendChild(card);
            });
            xmrNewsOffset += data.posts.length;
            if (data.has_more) {
                btn.style.display = 'inline-flex';
                btn.textContent = 'Load more';
                btn.disabled = false;
            } else {
                btn.style.display = 'none';
            }
        })
        .catch(function() {
            if (xmrNewsOffset === 0) {
                container.innerHTML = '<div style="text-align:center;padding:8px;opacity:0.7;">Failed to load news</div>';
            }
            btn.textContent = 'Load more';
            btn.disabled = false;
        });
}

function xmrLoadMoreNews() {
    var btn = document.getElementById('xmr-news-more');
    btn.textContent = 'Loading...';
    btn.disabled = true;
    xmrFetchNews();
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
            var exportBase = 'APP_ORIGIN_PLACEHOLDER/widget/UUID_PLACEHOLDER/export/';
            var btnStyle = 'display:inline-flex;align-items:center;gap:4px;font-size:10px;padding:3px 8px;border-radius:4px;border:1px solid ' + textColor + ';background:transparent;color:' + textColor + ';cursor:pointer;opacity:0.85;text-decoration:none;margin-right:4px;';
            var downloadsHtml =
                '<div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:4px;">' +
                '<a href="' + exportBase + 'csv" style="' + btnStyle + '">CSV</a>' +
                '<a href="' + exportBase + 'xml" style="' + btnStyle + '">XML</a>' +
                '<a href="' + exportBase + 'json" style="' + btnStyle + '">JSON</a>' +
                '</div>';
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

            var newsIconSvg = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px;"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/><path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M18 8h-8"/><path d="M15 12h-2"/></svg>';

            var newsSectionHtml = '';
            if (data.post_count > 0) {
                var newsLabel = newsIconSvg + ' News';
                if (data.fresh_posts_count > 0) {
                    newsLabel += ' <span style="display:inline-block;font-size:10px;font-weight:600;background:#FF6600;color:#fff;border-radius:8px;padding:1px 6px;margin-left:4px;vertical-align:middle;">+' + data.fresh_posts_count + '</span>';
                }
                newsSectionHtml =
                    '<div id="xmr-news-section" style="margin-top:16px;border-top:1px solid rgba(255,255,255,0.2);padding-top:12px;">' +
                    '<div onclick="xmrToggleNews()" style="cursor:pointer;display:flex;justify-content:space-between;align-items:center;user-select:none;">' +
                    '<span style="font-size:13px;font-weight:600;letter-spacing:0.3px;">' + newsLabel + '</span>' +
                    '<span id="xmr-news-arrow" style="font-size:11px;opacity:0.7;">' + '\u25bc' + '</span>' +
                    '</div>' +
                    '<div id="xmr-news-content" style="display:none;margin-top:10px;">' +
                    '<div id="xmr-news-posts"></div>' +
                    '<button id="xmr-news-more" onclick="xmrLoadMoreNews()" style="display:none;margin-top:8px;font-size:11px;padding:5px 14px;border-radius:6px;border:1px solid ' + textColor + ';background:transparent;color:' + textColor + ';cursor:pointer;opacity:0.85;">Load more</button>' +
                    '</div>' +
                    '</div>';
            }

            container.innerHTML = '<div style="' +
                'font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;' +
                'background: linear-gradient(135deg, ' + baseColor + ' 0%, ' + endColor + ' 100%);' +
                'color: ' + textColor + '; padding: 24px; border-radius: 12px;' +
                'box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 600px;' +
                '">' +
                '<div style="display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap;">' +
                '<div style="flex:1;min-width:200px;">' +
                '<div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">' +
                '&#128176; ' + data.label + '</div>' +
                (data.description ? '<div style="font-size: 12px; opacity: 0.8; margin-bottom: 6px;">' + data.description + '</div>' : '') +
                '<div style="font-size: 36px; font-weight: bold; margin-bottom: 8px;">' +
                data.total_received_xmr + ' XMR</div>' +
                progressHtml +
                '<div style="font-size: 12px; opacity: 0.8; margin-top: 8px;">' +
                'Updated: ' + data.last_updated + '</div>' +
                downloadsHtml +
                '</div>' +
                rightHtml +
                '</div>' +
                newsSectionHtml +
                '</div>';

            xmrNewsUuid = 'UUID_PLACEHOLDER';
            if (data.post_count > 0) {
                xmrNewsHasPosts = true;
            }
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


PUBLIC_EXPORT_FORMATS = {"xml", "csv", "json"}


async def _get_fund_by_uuid(uuid: str, db: AsyncSession) -> Fund:
    """Look up a fund by public_uuid, raise 404 if not found."""
    result = await db.execute(select(Fund).where(Fund.public_uuid == uuid))
    fund = result.scalar_one_or_none()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    return fund


@router.get("/widget/{uuid}/posts.json")
async def get_widget_posts(
    uuid: str,
    limit: int = Query(5, ge=1, le=20),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Public endpoint — paginated posts for the widget."""
    fund = await _get_fund_by_uuid(uuid, db)

    count_result = await db.execute(
        select(func.count(Post.id)).where(Post.fund_id == fund.id)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Post)
        .where(Post.fund_id == fund.id)
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    posts = result.scalars().all()

    return JSONResponse(
        content={
            "posts": [
                {
                    "id": str(p.id),
                    "body": p.body,
                    "created_at": p.created_at.strftime("%Y-%m-%d %H:%M UTC"),
                    "updated_at": (
                        p.updated_at.strftime("%Y-%m-%d %H:%M UTC")
                        if p.updated_at
                        else None
                    ),
                }
                for p in posts
            ],
            "total": total,
            "has_more": (offset + len(posts)) < total,
        },
        headers={
            "Cache-Control": "public, max-age=60",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/widget/{uuid}/export/{export_format}")
async def public_widget_export(
    uuid: str,
    export_format: str,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    tiers: str | None = Query(None),
    sort: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Public export endpoint for XML, CSV, JSON — no API key required.

    Lookup is by fund public_uuid so that embedded widgets can link directly.
    """
    if export_format not in PUBLIC_EXPORT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Public export only supports: {', '.join(sorted(PUBLIC_EXPORT_FORMATS))}. "
            f"Use the authenticated endpoint for PDF and XLSX.",
        )

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400, detail="start_date must be less than or equal to end_date"
        )

    fund = await _get_fund_by_uuid(uuid, db)

    # Parse optional filters
    tier_list: List[str] = []
    if tiers:
        from app.filters import VALID_TIER_NAMES

        tier_list = [t.strip().lower() for t in tiers.split(",") if t.strip()]
        invalid = [t for t in tier_list if t not in VALID_TIER_NAMES]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier names: {', '.join(invalid)}",
            )

    sort_rules: List[SortRule] = parse_sort(sort)

    # Fetch transactions
    query = select(Transaction).where(Transaction.fund_id == fund.id)
    date_filter = build_date_filter(start_date, end_date)
    if date_filter is not None:
        query = query.where(date_filter)
    tier_filter = build_tier_filter(tier_list)
    if tier_filter is not None:
        query = query.where(tier_filter)
    for clause in build_order_by(sort_rules):
        query = query.order_by(clause)
    result = await db.execute(query)
    transactions = result.scalars().all()

    total_xmr = sum(tx.amount_xmr for tx in transactions)

    # Overall stats
    stats_result = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount_xmr), 0).label("total"),
            func.count(Transaction.id).label("count"),
        ).where(Transaction.fund_id == fund.id)
    )
    stats_row = stats_result.one()
    overall_total = str(stats_row.total)

    filter_meta = describe_filters(start_date, end_date, tier_list, sort_rules)
    if not filter_meta.get("date_range"):
        filter_meta.pop("date_range", None)
    if not filter_meta.get("tiers"):
        filter_meta.pop("tiers", None)
    if not filter_meta.get("sort"):
        filter_meta.pop("sort", None)

    tx_dicts = [
        {
            "txid": tx.txid,
            "amount_atomic": tx.amount_atomic,
            "amount_xmr": str(tx.amount_xmr),
            "confirmations": tx.confirmations,
            "timestamp": tx.timestamp,
            "height": tx.height,
            "unlock_time": tx.unlock_time,
        }
        for tx in transactions
    ]

    dt_format = get_datetime_format()
    deposit_addr = fund.deposit_address or fund.primary_address
    fund_id_str = str(fund.id)
    filter_meta_or_none = filter_meta if filter_meta else None

    if export_format == "csv":
        data = generate_csv_export(
            transactions=tx_dicts,
            fund_label=fund.label,
            datetime_format=dt_format,
        )
        return Response(
            content=data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=export_{fund_id_str}.csv",
                "Access-Control-Allow-Origin": "*",
            },
        )

    elif export_format == "xml":
        data = generate_xml_report(
            fund_label=fund.label,
            transactions=tx_dicts,
            total_xmr=overall_total,
            datetime_format=dt_format,
            fund_description=fund.description,
            fund_id=fund_id_str,
            deposit_address=deposit_addr,
            filter_metadata=filter_meta_or_none,
        )
        return Response(
            content=data,
            media_type="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename=export_{fund_id_str}.xml",
                "Access-Control-Allow-Origin": "*",
            },
        )

    elif export_format == "json":
        data = generate_json_export(
            transactions=tx_dicts,
            fund_label=fund.label,
            fund_id=fund_id_str,
            datetime_format=dt_format,
            filter_metadata=filter_meta_or_none,
        )
        return Response(
            content=data,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=export_{fund_id_str}.json",
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

    post_count_result = await db.execute(
        select(func.count(Post.id)).where(Post.fund_id == fund.id)
    )
    post_count = post_count_result.scalar()

    time_threshold = datetime.now(timezone.utc) - timedelta(hours=24)
    fresh_posts_result = await db.execute(
        select(func.count(Post.id)).where(
            Post.fund_id == fund.id, Post.created_at >= time_threshold
        )
    )
    fresh_posts_count = fresh_posts_result.scalar()

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
        "post_count": post_count,
        "fresh_posts_count": fresh_posts_count,
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
