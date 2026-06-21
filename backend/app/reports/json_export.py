"""Generate JSON export for transaction data."""

import json
from datetime import datetime
from decimal import Decimal
from typing import List

from app.validators import format_datetime


class _DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal and datetime objects."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def generate_json_export(
    transactions: List[dict],
    fund_label: str,
    fund_id: str,
    datetime_format: str | None = None,
    filter_metadata: dict | None = None,
) -> str:
    """Generate a JSON string from filtered transaction data.

    Columns: txid, amount_atomic, amount_xmr, confirmations, timestamp, unlock_time, height.
    """
    formatted_txs = []
    for tx in transactions:
        ts = tx["timestamp"]
        if datetime_format and hasattr(ts, "year"):
            ts_str = format_datetime(ts, datetime_format)
        elif hasattr(ts, "isoformat"):
            ts_str = ts.isoformat()
        else:
            ts_str = str(ts)

        formatted_txs.append(
            {
                "txid": tx["txid"],
                "amount_atomic": tx["amount_atomic"],
                "amount_xmr": str(tx["amount_xmr"]),
                "confirmations": tx["confirmations"],
                "timestamp": ts_str,
                "unlock_time": tx.get("unlock_time") or 0,
                "height": tx["height"],
            }
        )

    result = {
        "fund_label": fund_label,
        "fund_id": fund_id,
        "generated_at": (
            format_datetime(datetime.now(), datetime_format)
            if datetime_format
            else datetime.now().isoformat()
        ),
        "transaction_count": len(formatted_txs),
        "filters": filter_metadata or {},
        "transactions": formatted_txs,
    }

    return json.dumps(result, indent=2, cls=_DecimalEncoder)
