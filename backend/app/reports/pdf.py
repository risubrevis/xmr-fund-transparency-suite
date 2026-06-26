"""Generate executive PDF report for transaction data."""

import io
from datetime import datetime
from typing import List

from jinja2 import Template

from app.validators import format_datetime

PDF_TEMPLATE = Template("""<!DOCTYPE html>
<html>
<head>
    <style>
        @page {
            size: A4;
            margin: 1.5cm;
        }
        body {
            font-family: Arial, sans-serif;
            color: #222;
            line-height: 1.4;
        }
        .header-section {
            border-bottom: 3px solid #f26822;
            padding-bottom: 16px;
            margin-bottom: 20px;
        }
        .header-section h1 {
            color: #f26822;
            margin: 0 0 4px 0;
            font-size: 22px;
        }
        .header-section .description {
            color: #555;
            font-size: 12px;
            margin-bottom: 12px;
        }
        .meta-list {
            font-size: 11px;
            color: #444;
        }
        .meta-list .row {
            margin-bottom: 3px;
        }
        .meta-list .label {
            font-weight: bold;
            color: #333;
        }

        .financial-summary {
            background: #f9f4ef;
            border: 1px solid #f26822;
            border-radius: 6px;
            padding: 14px 18px;
            margin-bottom: 20px;
        }
        .financial-summary h2 {
            color: #f26822;
            margin: 0 0 10px 0;
            font-size: 15px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px 24px;
            font-size: 12px;
        }
        .summary-grid .value {
            font-weight: bold;
            color: #222;
        }
        .filters-section {
            background: #f5f5f5;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px 14px;
            margin-bottom: 20px;
            font-size: 10px;
        }
        .filters-section h3 {
            margin: 0 0 6px 0;
            font-size: 11px;
            color: #555;
        }
        .filters-section ul {
            margin: 0;
            padding-left: 16px;
        }
        .filters-section li {
            margin-bottom: 2px;
            color: #444;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 10px;
        }
        th {
            background-color: #f26822;
            color: white;
            padding: 6px 8px;
            text-align: left;
            font-size: 10px;
        }
        td {
            border: 1px solid #ddd;
            padding: 5px 8px;
        }
        tr:nth-child(even) {
            background-color: #fafafa;
        }
        .table-footer td {
            font-weight: bold;
            background-color: #fff5eb;
            border-top: 2px solid #f26822;
        }
        .footer {
            margin-top: 30px;
            font-size: 9px;
            color: #999;
            text-align: center;
            border-top: 1px solid #ddd;
            padding-top: 8px;
        }
    </style>
</head>
<body>
    <div class="header-section">
        <h1>{{ fund_label }}</h1>
        {% if fund_description %}
        <div class="description">{{ fund_description }}</div>
        {% endif %}
        <div class="meta-list">
            <div class="row"><span class="label">Generated:</span> {{ generated_at }}</div>
            <div class="row"><span class="label">Deposit Address:</span> {{ deposit_address }}</div>
            <div class="row"><span class="label">Wallet&nbsp;Height:</span> {{ wallet_height }}</div>
        </div>
    </div>

    <div class="financial-summary">
        <h2>Financial Summary</h2>
        <div class="summary-grid">
            <div><span class="label">Total Received:</span> <span class="value">{{ total_xmr }} XMR</span></div>
            <div><span class="label">Target Amount:</span> <span class="value">{{ target_xmr or 'Not set' }}{% if target_xmr %} XMR{% endif %}</span></div>
            <div><span class="label">Transactions in Report:</span> <span class="value">{{ tx_count }}</span></div>
            <div><span class="label">Grand Total:</span> <span class="value">{{ grand_total }} XMR</span></div>
        </div>
    </div>

    {% if filter_metadata %}
    <div class="filters-section">
        <h3>Active Filters</h3>
        <ul>
            {% if filter_metadata.date_range %}
            <li>Date Range: {{ filter_metadata.date_range.start or '—' }} to {{ filter_metadata.date_range.end or '—' }}</li>
            {% endif %}
            {% if filter_metadata.tiers %}
            <li>Tiers: {% for t in filter_metadata.tiers %}{{ t.name }} ({{ t.range }}){% if not loop.last %}, {% endif %}{% endfor %}</li>
            {% endif %}
            {% if filter_metadata.sort %}
            <li>Sorted by: {% for s in filter_metadata.sort %}{{ s.field }} {{ s.direction }}{% if not loop.last %}, then {% endif %}{% endfor %}</li>
            {% endif %}
        </ul>
    </div>
    {% endif %}

    <h2 style="font-size: 14px; color: #333; margin-bottom: 8px;">Transactions</h2>
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Amount (XMR)</th>
                <th>Confirmations</th>
                <th>Timestamp</th>
                <th>Height</th>
            </tr>
        </thead>
        <tbody>
            {% for tx in transactions %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ tx.amount_xmr }}</td>
                <td>{{ tx.confirmations }}</td>
                <td>{{ tx.timestamp }}</td>
                <td>{{ tx.height }}</td>
            </tr>
            {% endfor %}
            {% if transactions %}
            <tr class="table-footer">
                <td colspan="1"><strong>Total</strong></td>
                <td><strong>{{ grand_total }} XMR</strong></td>
                <td colspan="3"></td>
            </tr>
            {% endif %}
        </tbody>
    </table>

    <div class="footer">
        Generated by XMR Fund Transparency Suite &mdash; Report reflects only the filtered/sorted subset of transactions.
    </div>
</body>
</html>
""")


def generate_pdf_report(
    fund_label: str,
    fund_description: str | None = None,
    deposit_address: str | None = None,
    wallet_height: int | None = None,
    transactions: List[dict] | None = None,
    total_xmr: str = "0",
    target_xmr: str | None = None,
    grand_total: str = "0",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    datetime_format: str | None = None,
    filter_metadata: dict | None = None,
) -> bytes:
    """Generate an executive PDF report with financial layout."""
    from weasyprint import HTML

    transactions = transactions or []
    now = datetime.now()
    generated_at = (
        format_datetime(now, datetime_format) if datetime_format else now.isoformat()
    )

    # Format transaction timestamps
    formatted_transactions = []
    for tx in transactions:
        tx_copy = dict(tx)
        if datetime_format and hasattr(tx_copy["timestamp"], "year"):
            tx_copy["timestamp"] = format_datetime(
                tx_copy["timestamp"], datetime_format
            )
        elif hasattr(tx_copy["timestamp"], "isoformat"):
            tx_copy["timestamp"] = tx_copy["timestamp"].isoformat()
        formatted_transactions.append(tx_copy)

    html_content = PDF_TEMPLATE.render(
        fund_label=fund_label,
        fund_description=fund_description,
        deposit_address=deposit_address or "—",
        wallet_height=str(wallet_height) if wallet_height is not None else "—",
        generated_at=generated_at,
        total_xmr=total_xmr,
        target_xmr=target_xmr,
        grand_total=grand_total,
        tx_count=len(formatted_transactions),
        transactions=formatted_transactions,
        filter_metadata=filter_metadata,
    )

    pdf_file = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_file)
    pdf_file.seek(0)
    return pdf_file.read()
