"""Legacy report endpoints (PDF, XML) — backward-compatible.

For the new export system with filtering and multi-format support, see exports.py.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
from app.logging import get_logger
from app.models import Fund, Transaction
from app.reports.pdf import generate_pdf_report
from app.reports.xml import generate_xml_report
from app.settings import get_datetime_format

logger = get_logger("api.reports")
router = APIRouter()


@router.get("/funds/{fund_id}/report.pdf")
async def get_pdf_report(
    fund_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> Response:
    """Generate and download PDF report for a fund (all transactions, no filters)."""
    result = await db.execute(select(Fund).where(Fund.id == fund_id))
    fund = result.scalar_one_or_none()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    tx_result = await db.execute(
        select(Transaction)
        .where(Transaction.fund_id == fund_id)
        .order_by(Transaction.timestamp.desc())
    )
    transactions = tx_result.scalars().all()

    total_xmr = sum(tx.amount_xmr for tx in transactions)
    deposit_addr = fund.deposit_address
    dt_format = get_datetime_format()

    pdf_data = generate_pdf_report(
        fund_label=fund.label,
        fund_description=fund.description,
        deposit_address=deposit_addr,
        wallet_height=None,
        transactions=[
            {
                "txid": tx.txid,
                "amount_atomic": tx.amount_atomic,
                "amount_xmr": str(tx.amount_xmr),
                "timestamp": tx.timestamp,
                "confirmations": tx.confirmations,
                "height": tx.height,
                "unlock_time": tx.unlock_time,
            }
            for tx in transactions
        ],
        total_xmr=str(total_xmr),
        target_xmr=str(fund.target_amount_xmr) if fund.target_amount_xmr else None,
        grand_total=str(total_xmr),
        datetime_format=dt_format,
    )

    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{fund_id}.pdf"},
    )


@router.get("/funds/{fund_id}/report.xml")
async def get_xml_report(
    fund_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> Response:
    """Generate and download XML report for a fund (all transactions, no filters)."""
    result = await db.execute(select(Fund).where(Fund.id == fund_id))
    fund = result.scalar_one_or_none()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    tx_result = await db.execute(
        select(Transaction)
        .where(Transaction.fund_id == fund_id)
        .order_by(Transaction.timestamp.desc())
    )
    transactions = tx_result.scalars().all()

    total_xmr = sum(tx.amount_xmr for tx in transactions)
    deposit_addr = fund.deposit_address
    dt_format = get_datetime_format()

    xml_data = generate_xml_report(
        fund_label=fund.label,
        transactions=[
            {
                "txid": tx.txid,
                "amount_atomic": tx.amount_atomic,
                "amount_xmr": str(tx.amount_xmr),
                "timestamp": tx.timestamp,
                "confirmations": tx.confirmations,
                "height": tx.height,
                "unlock_time": tx.unlock_time,
            }
            for tx in transactions
        ],
        total_xmr=str(total_xmr),
        datetime_format=dt_format,
        fund_description=fund.description,
        fund_id=str(fund_id),
        deposit_address=deposit_addr,
    )

    return Response(
        content=xml_data,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=report_{fund_id}.xml"},
    )
