"""Tests for the XML report generator."""

from datetime import datetime, timezone

from app.reports.xml import generate_xml_report


class TestXmlReport:
    def test_generate_xml_report_basic(self):
        transactions = [
            {
                "txid": "a" * 64,
                "amount_xmr": "15.000000000000",
                "timestamp": datetime(2026, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
                "confirmations": 128,
                "height": 3280400,
            },
            {
                "txid": "b" * 64,
                "amount_xmr": "230.000000000000",
                "timestamp": datetime(2026, 6, 14, 18, 22, 0, tzinfo=timezone.utc),
                "confirmations": 245,
                "height": 3280390,
            },
        ]

        result = generate_xml_report(
            fund_label="Test Fund",
            transactions=transactions,
            total_xmr="245.000000000000",
        )

        assert "Test Fund" in result
        assert "245.000000000000" in result
        assert "2" in result  # transaction count
        assert "fund_report" in result
        assert "transaction" in result

    def test_generate_xml_report_empty_transactions(self):
        result = generate_xml_report(
            fund_label="Empty Fund",
            transactions=[],
            total_xmr="0",
        )

        assert "Empty Fund" in result
        assert "0" in result
