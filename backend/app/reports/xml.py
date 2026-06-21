"""Generate XML export for transaction data."""

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
    fund_description: str | None = None,
    fund_id: str | None = None,
    deposit_address: str | None = None,
    filter_metadata: dict | None = None,
) -> str:
    """Generate XML report from transaction data."""
    root = Element("fund_report")
    root.set("xmlns", "https://xmr-fund-transparency.example/schema")

    # Metadata
    meta = SubElement(root, "metadata")

    fund_label_elem = SubElement(meta, "fund_label")
    fund_label_elem.text = fund_label

    if fund_description:
        desc_elem = SubElement(meta, "fund_description")
        desc_elem.text = fund_description

    if fund_id:
        id_elem = SubElement(meta, "fund_id")
        id_elem.text = fund_id

    if deposit_address:
        addr_elem = SubElement(meta, "deposit_address")
        addr_elem.text = deposit_address

    generated_at = SubElement(meta, "generated_at")
    now = datetime.now()
    generated_at.text = (
        format_datetime(now, datetime_format) if datetime_format else now.isoformat()
    )

    total = SubElement(meta, "total_received_xmr")
    total.text = total_xmr

    tx_count = SubElement(meta, "transaction_count")
    tx_count.text = str(len(transactions))

    # Filter metadata
    if filter_metadata:
        filters_elem = SubElement(meta, "filters")
        if filter_metadata.get("date_range"):
            dr = filter_metadata["date_range"]
            date_range_elem = SubElement(filters_elem, "date_range")
            if dr.get("start"):
                start_elem = SubElement(date_range_elem, "start")
                start_elem.text = dr["start"]
            if dr.get("end"):
                end_elem = SubElement(date_range_elem, "end")
                end_elem.text = dr["end"]
        if filter_metadata.get("tiers"):
            tiers_elem = SubElement(filters_elem, "tiers")
            for t in filter_metadata["tiers"]:
                tier_elem = SubElement(tiers_elem, "tier")
                tier_elem.set("name", t["name"])
                tier_elem.set("range", t["range"])
        if filter_metadata.get("sort"):
            sort_elem = SubElement(filters_elem, "sort")
            for s in filter_metadata["sort"]:
                rule_elem = SubElement(sort_elem, "rule")
                rule_elem.set("field", s["field"])
                rule_elem.set("direction", s["direction"])

    # Transactions
    txs_elem = SubElement(root, "transactions")
    for tx in transactions:
        tx_elem = SubElement(txs_elem, "transaction")

        txid = SubElement(tx_elem, "txid")
        txid.text = tx["txid"]

        amount_atomic = SubElement(tx_elem, "amount_atomic")
        amount_atomic.text = str(tx.get("amount_atomic", ""))

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

        unlock_time = SubElement(tx_elem, "unlock_time")
        unlock_time.text = str(tx.get("unlock_time") or 0)

    xml_str = tostring(root, encoding="unicode")
    parsed = minidom.parseString(xml_str)
    return parsed.toprettyxml(indent="  ")
