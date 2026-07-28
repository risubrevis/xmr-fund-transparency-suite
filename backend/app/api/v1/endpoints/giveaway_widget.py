"""Public (no-auth) embeddable widget endpoints for giveaways.

Routes (mounted at root, no /api/v1 prefix):
    GET /widget/giveaway/{public_uuid}.js        — embeddable JS widget
    GET /widget/giveaway/{public_uuid}.json      — widget data
    GET /widget/giveaway/{public_uuid}/export/{format} — public export (pdf, xlsx, csv, xml, json)

The widget has two states:
  * active  (now < end_date): countdown + entry info + QR
  * closed  (is_closed): winner announcement + provable-fair seed + instructions
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Giveaway, Post, Transaction
from app.reports.csv_export import generate_csv_export
from app.reports.json_export import generate_json_export
from app.reports.pdf import generate_pdf_report
from app.reports.xlsx import generate_xlsx_export
from app.reports.xml import generate_xml_report
from app.services.qr import generate_qr_data_url
from app.settings import get_datetime_format

DEFAULT_WIDGET_BG_COLOR = "#667eea"
DEFAULT_WIDGET_TEXT_COLOR = "#ffffff"

router = APIRouter()


async def _get_giveaway_by_uuid(public_uuid: str, db: AsyncSession) -> Giveaway:
    res = await db.execute(select(Giveaway).where(Giveaway.public_uuid == public_uuid))
    giveaway = res.scalar_one_or_none()
    if not giveaway:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    return giveaway


GIVEAWAY_WIDGET_JS_TEMPLATE = """
function xmrGiveawayCopyAddr(btn) {
    var addr = btn.getAttribute('data-addr');
    function done() { btn.textContent = 'Copy Address'; }
    function fallback() {
        var ta = document.createElement('textarea');
        ta.value = addr;
        ta.style.position = 'fixed'; ta.style.left = '-9999px'; ta.style.opacity = '0';
        document.body.appendChild(ta); ta.focus(); ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        btn.textContent = 'Copied!'; setTimeout(done, 2000);
    }
    try {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(addr).then(function() {
                btn.textContent = 'Copied!'; setTimeout(done, 2000);
            }).catch(fallback);
        } else { fallback(); }
    } catch(e) { fallback(); }
}

function xmrFmtTs(iso) {
    if (!iso) return '';
    var d = new Date(iso);
    if (isNaN(d)) return iso;
    return d.toLocaleString(undefined, {year:'numeric',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});
}

function xmrFmtCountdown(ms) {
    if (ms <= 0) return '00:00:00';
    var s = Math.floor(ms/1000);
    var d = Math.floor(s/86400); s -= d*86400;
    var h = Math.floor(s/3600); s -= h*3600;
    var m = Math.floor(s/60); s -= m*60;
    var parts = [];
    if (d>0) parts.push(d+'d');
    parts.push(String(h).padStart(2,'0'));
    parts.push(String(m).padStart(2,'0'));
    parts.push(String(s).padStart(2,'0'));
    return parts.join(':');
}

var xmrGiveawayNewsOffset = 0;
var xmrGiveawayNewsUuid = '';

function xmrGiveawayToggleNews() {
    var content = document.getElementById('xmr-giveaway-news-content');
    var arrow = document.getElementById('xmr-giveaway-news-arrow');
    if (!content || !arrow) return;
    if (content.style.display === 'none') {
        content.style.display = 'block';
        arrow.textContent = '\u25b2';
        xmrGiveawayNewsOffset = 0;
        xmrGiveawayFetchNews();
    } else {
        content.style.display = 'none';
        arrow.textContent = '\u25bc';
        var c = document.getElementById('xmr-giveaway-news-posts'); if (c) c.innerHTML = '';
        var b = document.getElementById('xmr-giveaway-news-more'); if (b) b.style.display = 'none';
    }
}

function xmrGiveawayFetchNews() {
    var container = document.getElementById('xmr-giveaway-news-posts');
    if (!container) return;
    if (xmrGiveawayNewsOffset === 0) {
        container.innerHTML = '<div style="text-align:center;padding:8px;opacity:0.7;">Loading...</div>';
    }
    var btn = document.getElementById('xmr-giveaway-news-more');
    var base = 'APP_ORIGIN_PLACEHOLDER/widget/giveaway/' + xmrGiveawayNewsUuid;
    fetch(base + '/posts.json?limit=5&offset=' + xmrGiveawayNewsOffset)
        .then(function(r){ return r.json(); })
        .then(function(data) {
            if (xmrGiveawayNewsOffset === 0) container.innerHTML = '';
            if (data.posts.length === 0 && xmrGiveawayNewsOffset === 0) {
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
                card.appendChild(dateEl); card.appendChild(bodyEl);
                container.appendChild(card);
            });
            xmrGiveawayNewsOffset += data.posts.length;
            if (data.has_more) { btn.style.display = 'inline-flex'; btn.textContent = 'Load more'; btn.disabled = false; }
            else { btn.style.display = 'none'; }
        })
        .catch(function() {
            if (xmrGiveawayNewsOffset === 0) container.innerHTML = '<div style="text-align:center;padding:8px;opacity:0.7;">Failed to load news</div>';
            if (btn) { btn.textContent = 'Load more'; btn.disabled = false; }
        });
}

function xmrGiveawayLoadMoreNews() {
    var b = document.getElementById('xmr-giveaway-news-more');
    b.textContent = 'Loading...'; b.disabled = true;
    xmrGiveawayFetchNews();
}

(function() {
    var container = document.getElementById('xmr-giveaway-widget');
    if (!container) return;

    function hexToHsl(hex) {
        var r = parseInt(hex.slice(1,3),16)/255, g = parseInt(hex.slice(3,5),16)/255, b = parseInt(hex.slice(5,7),16)/255;
        var max = Math.max(r,g,b), min = Math.min(r,g,b); var h,s,l=(max+min)/2;
        if (max===min){h=s=0;} else {var d=max-min; s=l>0.5?d/(2-max-min):d/(max+min);
            if(max===r)h=((g-b)/d+(g<b?6:0))/6; else if(max===g)h=((b-r)/d+2)/6; else h=((r-g)/d+4)/6;}
        return [h*360,s*100,l*100];
    }
    function hslToHex(h,s,l){h=((h%360)+360)%360;s/=100;l/=100;var c=(1-Math.abs(2*l-1))*s;var x=c*(1-Math.abs((h/60)%2-1));var m=l-c/2;var r,g,b;
        if(h<60){r=c;g=x;b=0;} else if(h<120){r=x;g=c;b=0;} else if(h<180){r=0;g=c;b=x;} else if(h<240){r=0;g=x;b=c;} else if(h<300){r=x;g=0;b=c;} else {r=c;g=0;b=x;}
        var toHex=function(v){return Math.round((v+m)*255).toString(16).padStart(2,'0');}; return '#'+toHex(r)+toHex(g)+toHex(b);}
    function shiftHue(hex,deg){var hsl=hexToHsl(hex);return hslToHex(hsl[0]+deg,hsl[1],hsl[2]);}

    var exportBase = 'APP_ORIGIN_PLACEHOLDER/widget/giveaway/UUID_PLACEHOLDER/export/';
    var btnStyle = 'display:inline-flex;align-items:center;gap:4px;font-size:10px;padding:3px 8px;border-radius:4px;border:1px solid TEXT_COLOR_PLACEHOLDER;background:transparent;color:TEXT_COLOR_PLACEHOLDER;cursor:pointer;opacity:0.85;text-decoration:none;margin-right:4px;';
    function btn(href,label){return '<a href="'+href+'" style="'+btnStyle+'">'+label+'</a>';}
    var downloadsHtml = '<div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:4px;">' +
        btn(exportBase+'pdf','PDF') + btn(exportBase+'xlsx','XLSX') + btn(exportBase+'csv','CSV') + btn(exportBase+'xml','XML') + btn(exportBase+'json','JSON') + '</div>';

    fetch('APP_ORIGIN_PLACEHOLDER/widget/giveaway/UUID_PLACEHOLDER.json')
        .then(function(r){return r.json();})
        .then(function(data){
            var baseColor = data.base_color || '#667eea';
            var textColor = data.text_color || '#ffffff';
            var endColor = shiftHue(baseColor, 40);
            var btnStyleLocal = btnStyle.split('TEXT_COLOR_PLACEHOLDER').join(textColor);
            downloadsHtml = downloadsHtml.split('TEXT_COLOR_PLACEHOLDER').join(textColor);

            var addrShort = data.deposit_address.slice(0,10)+'...'+data.deposit_address.slice(-10);
            var rightHtml = '<div style="display:flex;flex-direction:column;align-items:center;min-width:140px;">' +
                '<img src="'+data.qr_code+'" alt="QR Code" style="width:140px;height:140px;border-radius:8px;background:#fff;padding:4px;" />' +
                '<div style="font-size:10px;opacity:0.7;word-break:break-all;margin-top:8px;text-align:center;">'+addrShort+'</div>' +
                '<button data-addr="'+data.deposit_address+'" onclick="xmrGiveawayCopyAddr(this)" '+
                'style="margin-top:6px;font-size:11px;padding:4px 10px;border-radius:6px;border:1px solid '+textColor+';background:transparent;color:'+textColor+';cursor:pointer;opacity:0.9;">Copy Address</button>' +
                '</div>';

            var body = '';
            if (data.is_closed) {
                body = '<div style="flex:1;min-width:200px;">' +
                    '<div style="font-size:14px;opacity:0.9;margin-bottom:8px;">&#127942; '+data.title+'</div>' +
                    (data.description ? '<div style="font-size:12px;opacity:0.8;margin-bottom:6px;">'+data.description+'</div>' : '') +
                    '<div style="font-size:13px;font-weight:600;margin-top:10px;margin-bottom:6px;">Giveaway Closed — Winner</div>';
                if (data.winner && data.winner.winning_txid) {
                    body += '<div style="font-size:11px;opacity:0.85;margin-bottom:4px;">Winning tx: <span style="font-family:monospace;">'+data.winner.winning_txid.slice(0,16)+'...'+data.winner.winning_txid.slice(-8)+'</span></div>' +
                        '<div style="font-size:13px;font-weight:600;">'+data.winner.winning_amount_xmr+' XMR</div>' +
                        '<div style="font-size:11px;opacity:0.7;margin-top:2px;">'+xmrFmtTs(data.winner.winning_timestamp)+'</div>';
                } else {
                    body += '<div style="font-size:12px;opacity:0.8;">No eligible entries were recorded for this giveaway.</div>';
                }
                body += '<div style="margin-top:10px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.2);font-size:11px;opacity:0.85;">' +
                    '<div style="font-weight:600;margin-bottom:2px;">Provably fair seed block</div>' +
                    '<div>Height: <span style="font-family:monospace;">'+(data.winning_block_height||'—')+'</span></div>' +
                    '<div style="word-break:break-all;">Hash: <span style="font-family:monospace;font-size:10px;">'+(data.winning_block_hash||'—')+'</span></div>' +
                    '<div style="font-size:10px;opacity:0.7;margin-top:2px;">Eligible entries: '+data.eligible_count+'</div>' +
                    '</div>';
                if (data.instructions_after_end) {
                    body += '<div style="margin-top:10px;padding:8px;background:rgba(255,255,255,0.12);border-radius:8px;font-size:12px;white-space:pre-wrap;line-height:1.5;">'+data.instructions_after_end+'</div>';
                }
                body += downloadsHtml + '</div>';
            } else {
                body = '<div style="flex:1;min-width:200px;">' +
                    '<div style="font-size:14px;opacity:0.9;margin-bottom:8px;">&#127873; '+data.title+'</div>' +
                    (data.description ? '<div style="font-size:12px;opacity:0.8;margin-bottom:6px;">'+data.description+'</div>' : '') +
                    '<div style="font-size:11px;opacity:0.85;margin-bottom:4px;">Min entry: <b>'+data.min_amount_xmr+' XMR</b> · Entries: <b>'+data.eligible_count+'</b></div>' +
                    '<div id="xmr-giveaway-countdown" style="font-size:24px;font-weight:bold;letter-spacing:1px;margin:6px 0;">'+xmrFmtCountdown(data.remaining_ms)+'</div>' +
                    '<div style="font-size:11px;opacity:0.8;">Starts: '+xmrFmtTs(data.start_date)+'</div>' +
                    '<div style="font-size:11px;opacity:0.8;">Ends: '+xmrFmtTs(data.end_date)+'</div>' +
                    '<div style="font-size:12px;opacity:0.85;margin-top:6px;">Total received: '+data.total_received_xmr+' XMR</div>' +
                    downloadsHtml + '</div>';
            }

            var newsIconSvg = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/><path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M18 8h-8"/><path d="M15 12h-2"/></svg>';
            var newsSectionHtml = '';
            if (data.post_count > 0) {
                var newsLabel = newsIconSvg + '<span style="white-space:nowrap;">News</span>';
                if (data.fresh_posts_count > 0) {
                    newsLabel += '<span style="display:inline-flex;align-items:center;font-size:10px;font-weight:600;background:#FF6600;color:#fff;border-radius:8px;padding:1px 6px;flex-shrink:0;">+' + data.fresh_posts_count + '</span>';
                }
                newsSectionHtml = '<div id="xmr-giveaway-news-section" style="margin-top:16px;border-top:1px solid rgba(255,255,255,0.2);padding-top:12px;">' +
                    '<div onclick="xmrGiveawayToggleNews()" style="cursor:pointer;display:flex;justify-content:space-between;align-items:center;user-select:none;">' +
                    '<span style="font-size:13px;font-weight:600;letter-spacing:0.3px;display:inline-flex;align-items:center;flex-wrap:nowrap;gap:4px;">' + newsLabel + '</span>' +
                    '<span id="xmr-giveaway-news-arrow" style="font-size:11px;opacity:0.7;">\u25bc</span>' +
                    '</div>' +
                    '<div id="xmr-giveaway-news-content" style="display:none;margin-top:10px;">' +
                    '<div id="xmr-giveaway-news-posts"></div>' +
                    '<button id="xmr-giveaway-news-more" onclick="xmrGiveawayLoadMoreNews()" style="display:none;margin-top:8px;font-size:11px;padding:5px 14px;border-radius:6px;border:1px solid ' + textColor + ';background:transparent;color:' + textColor + ';cursor:pointer;opacity:0.85;">Load more</button>' +
                    '</div>' +
                    '</div>';
            }

            container.innerHTML = '<div style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;' +
                'background:linear-gradient(135deg,'+baseColor+' 0%,'+endColor+' 100%);' +
                'color:'+textColor+';padding:24px;border-radius:12px;box-shadow:0 4px 6px rgba(0,0,0,0.1);width:100%;display:flex;flex-direction:column;">' +
                '<div style="display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap;">' +
                body + rightHtml +
                '</div>' +
                newsSectionHtml +
                '<div style="font-size:11px;opacity:0.6;padding-top:12px;"><a href="https://xmrfts.com" target="_blank" rel="noopener noreferrer" style="color:inherit;text-decoration:none;">Giveaway widget powered by xmrfts.com</a></div>' +
                '</div>';

            xmrGiveawayNewsUuid = 'UUID_PLACEHOLDER';

            if (!data.is_closed && data.remaining_ms > 0) {
                var el = document.getElementById('xmr-giveaway-countdown');
                if (el) {
                    var endMs = new Date(data.end_date).getTime();
                    setInterval(function(){
                        var rem = endMs - Date.now();
                        el.textContent = xmrFmtCountdown(rem);
                    }, 1000);
                }
            }
        })
        .catch(function(){
            container.innerHTML = '<div style="color:red;">Failed to load giveaway widget</div>';
        });
})();
"""


@router.get("/widget/giveaway/{public_uuid}.js")
async def get_giveaway_widget_js(
    public_uuid: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    await _get_giveaway_by_uuid(public_uuid, db)
    origin = settings.app_origin
    widget_js = GIVEAWAY_WIDGET_JS_TEMPLATE.replace(
        "UUID_PLACEHOLDER", public_uuid
    ).replace("APP_ORIGIN_PLACEHOLDER", origin)
    return Response(
        content=widget_js,
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/widget/giveaway/{public_uuid}.json")
async def get_giveaway_widget_json(
    public_uuid: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    giveaway = await _get_giveaway_by_uuid(public_uuid, db)

    total_res = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount_xmr), 0)).where(
            Transaction.giveaway_id == giveaway.id
        )
    )
    total_xmr = total_res.scalar()

    eligible_res = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.giveaway_id == giveaway.id,
            Transaction.timestamp >= giveaway.start_date,
            Transaction.timestamp <= giveaway.end_date,
            Transaction.amount_xmr >= Decimal(giveaway.min_amount_xmr),
        )
    )
    eligible_count = int(eligible_res.scalar() or 0)

    winner = None
    if giveaway.is_closed and giveaway.winning_transaction_id is not None:
        wres = await db.execute(
            select(Transaction).where(Transaction.id == giveaway.winning_transaction_id)
        )
        wtx = wres.scalar_one_or_none()
        if wtx is not None:
            winner = {
                "winning_txid": wtx.txid,
                "winning_amount_xmr": f"{wtx.amount_xmr:.4f}",
                "winning_timestamp": wtx.timestamp.isoformat(),
            }

    now = datetime.now(timezone.utc)
    remaining_ms = max(
        0, int(giveaway.end_date.timestamp() * 1000) - int(now.timestamp() * 1000)
    )

    post_count_res = await db.execute(
        select(func.count(Post.id)).where(Post.giveaway_id == giveaway.id)
    )
    post_count = int(post_count_res.scalar() or 0)
    fresh_threshold = now - timedelta(hours=24)
    fresh_posts_res = await db.execute(
        select(func.count(Post.id)).where(
            Post.giveaway_id == giveaway.id, Post.created_at >= fresh_threshold
        )
    )
    fresh_posts_count = int(fresh_posts_res.scalar() or 0)

    data = {
        "title": giveaway.title,
        "description": giveaway.description or "",
        "deposit_address": giveaway.deposit_address,
        "qr_code": generate_qr_data_url(f"monero:{giveaway.deposit_address}"),
        "min_amount_xmr": f"{giveaway.min_amount_xmr:.4f}",
        "start_date": giveaway.start_date.isoformat(),
        "end_date": giveaway.end_date.isoformat(),
        "total_received_xmr": f"{total_xmr:.4f}",
        "eligible_count": eligible_count,
        "is_closed": giveaway.is_closed,
        "remaining_ms": remaining_ms,
        "winning_block_height": giveaway.winning_block_height,
        "winning_block_hash": giveaway.winning_block_hash,
        "instructions_after_end": giveaway.instructions_after_end,
        "winner": winner,
        "post_count": post_count,
        "fresh_posts_count": fresh_posts_count,
        "last_updated": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "base_color": giveaway.widget_background_color or DEFAULT_WIDGET_BG_COLOR,
        "text_color": giveaway.widget_text_color or DEFAULT_WIDGET_TEXT_COLOR,
        "public_website": giveaway.public_website,
    }
    return JSONResponse(
        content=data,
        headers={"Cache-Control": "public, max-age=30"},
    )


PUBLIC_EXPORT_FORMATS = {"pdf", "xlsx", "csv", "xml", "json"}


@router.get("/widget/giveaway/{public_uuid}/export/{export_format}")
async def public_giveaway_export(
    public_uuid: str,
    export_format: str,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Public export of transactions recorded for a giveaway (pdf, xlsx, csv, xml, json)."""
    if export_format not in PUBLIC_EXPORT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Public export only supports: {', '.join(sorted(PUBLIC_EXPORT_FORMATS))}.",
        )
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400, detail="start_date must be less than or equal to end_date"
        )

    giveaway = await _get_giveaway_by_uuid(public_uuid, db)

    query = select(Transaction).where(Transaction.giveaway_id == giveaway.id)
    if start_date is not None:
        query = query.where(Transaction.timestamp >= start_date)
    if end_date is not None:
        query = query.where(Transaction.timestamp <= end_date)
    query = query.order_by(Transaction.timestamp.desc())
    result = await db.execute(query)
    transactions = result.scalars().all()

    stats_result = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount_xmr), 0).label("total"),
            func.count(Transaction.id).label("count"),
        ).where(Transaction.giveaway_id == giveaway.id)
    )
    stats_row = stats_result.one()
    overall_total = str(stats_row.total)

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
    gid = str(giveaway.id)
    deposit_addr = giveaway.deposit_address
    grand_total = str(sum(tx.amount_xmr for tx in transactions))

    if export_format == "pdf":
        data = generate_pdf_report(
            fund_label=giveaway.title,
            fund_description=giveaway.description,
            deposit_address=deposit_addr,
            wallet_height=None,
            transactions=tx_dicts,
            total_xmr=overall_total,
            target_xmr=None,
            grand_total=grand_total,
            date_from=start_date,
            date_to=end_date,
            datetime_format=dt_format,
            filter_metadata=None,
        )
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=giveaway_{gid}.pdf"},
        )
    if export_format == "xlsx":
        data = generate_xlsx_export(
            transactions=tx_dicts,
            fund_label=giveaway.title,
            datetime_format=dt_format,
        )
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=giveaway_{gid}.xlsx"
            },
        )
    if export_format == "csv":
        data = generate_csv_export(
            transactions=tx_dicts,
            fund_label=giveaway.title,
            datetime_format=dt_format,
        )
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=giveaway_{gid}.csv"},
        )
    if export_format == "xml":
        data = generate_xml_report(
            fund_label=giveaway.title,
            transactions=tx_dicts,
            total_xmr=overall_total,
            datetime_format=dt_format,
            fund_description=giveaway.description,
            fund_id=gid,
            deposit_address=giveaway.deposit_address,
            filter_metadata=None,
        )
        return Response(
            content=data,
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename=giveaway_{gid}.xml"},
        )
    # json
    data = generate_json_export(
        transactions=tx_dicts,
        fund_label=giveaway.title,
        fund_id=gid,
        datetime_format=dt_format,
        filter_metadata=None,
    )
    return Response(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=giveaway_{gid}.json"},
    )


@router.get("/widget/giveaway/{public_uuid}/posts.json")
async def get_giveaway_widget_posts(
    public_uuid: str,
    limit: int = Query(5, ge=1, le=20),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Public endpoint — paginated news posts for the giveaway widget."""
    giveaway = await _get_giveaway_by_uuid(public_uuid, db)

    count_result = await db.execute(
        select(func.count(Post.id)).where(Post.giveaway_id == giveaway.id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Post)
        .where(Post.giveaway_id == giveaway.id)
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
        headers={"Cache-Control": "public, max-age=60"},
    )
