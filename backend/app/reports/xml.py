from datetime import datetime
from typing import List
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

from app.validators import format_datetime


def generate_xml_report(
    fund_label: str,
    transactions: List[dict],
    total_xmr: str,
    datetime_format: str | None = None,
) -> str:
    """Generate XML report from transaction data."""
    root = Element("fund_report")
    root.set("xmlns", "https://xmr-fund-transparency.example/schema")

    # Metadata
    meta = SubElement(root, "metadata")

    fund_label_elem = SubElement(meta, "fund_label")
    fund_label_elem.text = fund_label

    generated_at = SubElement(meta, "generated_at")
    now = datetime.now()
    generated_at.text = (
        format_datetime(now, datetime_format) if datetime_format else now.isoformat()
    )

    total = SubElement(meta, "total_received_xmr")
    total.text = total_xmr

    tx_count = SubElement(meta, "transaction_count")
    tx_count.text = str(len(transactions))

    # Transactions
    txs_elem = SubElement(root, "transactions")
    for tx in transactions:
        tx_elem = SubElement(txs_elem, "transaction")

        txid = SubElement(tx_elem, "txid")
        txid.text = tx["txid"]

        amount = SubElement(tx_elem, "amount_xmr")
        amount.text = str(tx["amount_xmr"])

        timestamp = SubElement(tx_elem, "timestamp")
        if datetime_format and hasattr(tx["timestamp"], "year"):
            timestamp.text = format_datetime(tx["timestamp"], datetime_format)
        elif hasattr(tx["timestamp"], "isoformat"):
            timestamp.text = tx["timestamp"].isoformat()
        else:
            timestamp.text = str(tx["timestamp"])

        confirmations = SubElement(tx_elem, "confirmations")
        confirmations.text = str(tx["confirmations"])

        height = SubElement(tx_elem, "height")
        height.text = str(tx["height"])

    xml_str = tostring(root, encoding="unicode")
    parsed = minidom.parseString(xml_str)
    return parsed.toprettyxml(indent="  ")
