"""Generate CSV export for transaction data."""

import csv
import io
from typing import List

from app.validators import format_datetime


def generate_csv_export(
    transactions: List[dict],
    fund_label: str,
    datetime_format: str | None = None,
) -> str:
    """Generate a CSV string from filtered transaction data.

    Columns: txid, amount_atomic, amount_xmr, confirmations, timestamp, unlock_time, height.
    """
    headers = [
        "txid",
        "amount_atomic",
        "amount_xmr",
        "confirmations",
        "timestamp",
        "unlock_time",
        "height",
    ]

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(headers)

    for tx in transactions:
        ts = tx["timestamp"]
        if datetime_format and hasattr(ts, "year"):
            ts_str = format_datetime(ts, datetime_format)
        elif hasattr(ts, "isoformat"):
            ts_str = ts.isoformat()
        else:
            ts_str = str(ts)

        writer.writerow(
            [
                tx["txid"],
                tx["amount_atomic"],
                str(tx["amount_xmr"]),
                tx["confirmations"],
                ts_str,
                tx.get("unlock_time") or 0,
                tx["height"],
            ]
        )

    return output.getvalue()
