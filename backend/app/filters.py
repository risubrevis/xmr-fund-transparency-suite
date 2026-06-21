"""Shared filter/sort logic for transaction queries and exports."""

from datetime import datetime
from decimal import Decimal
from typing import NamedTuple

from sqlalchemy import ColumnElement, and_, or_
from sqlalchemy import asc as sa_asc
from sqlalchemy import desc as sa_desc

from app.models import Transaction

# Tier definitions: name -> (lower_bound, upper_bound) in XMR
# micro:  < 0.1
# medium: >= 0.1 and <= 1.0
# large:  > 1.0 and <= 5.0
# whale:  > 5.0
TIERS: dict[str, tuple[Decimal | None, Decimal | None]] = {
    "micro": (None, Decimal("0.1")),
    "medium": (Decimal("0.1"), Decimal("1.0")),
    "large": (Decimal("1.0"), Decimal("5.0")),
    "whale": (Decimal("5.0"), None),
}

VALID_TIER_NAMES = set(TIERS.keys())

# Allowed sort columns mapped to Transaction model attributes
SORT_COLUMNS: dict[str, ColumnElement] = {
    "timestamp": Transaction.timestamp,
    "amount_xmr": Transaction.amount_xmr,
    "confirmations": Transaction.confirmations,
    "height": Transaction.height,
}

VALID_SORT_DIRECTIONS = {"asc", "desc"}


class SortRule(NamedTuple):
    column: str
    direction: str


def parse_sort(sort_str: str | None) -> list[SortRule]:
    """Parse a comma-separated sort string like 'timestamp:desc,amount_xmr:asc'.

    Returns a list of SortRule namedtuples.
    Invalid entries are silently skipped.
    """
    if not sort_str:
        return []

    rules: list[SortRule] = []
    for part in sort_str.split(","):
        part = part.strip()
        if ":" not in part:
            continue
        col, direction = part.rsplit(":", 1)
        col = col.strip()
        direction = direction.strip().lower()
        if col in SORT_COLUMNS and direction in VALID_SORT_DIRECTIONS:
            rules.append(SortRule(column=col, direction=direction))
    return rules


def build_tier_filter(tiers: list[str]) -> ColumnElement | None:
    """Build a SQLAlchemy WHERE clause from selected tier names.

    Returns None if no valid tiers are provided (i.e., no tier filter applied).
    """
    conditions: list[ColumnElement] = []
    for tier_name in tiers:
        tier_name = tier_name.strip().lower()
        if tier_name not in TIERS:
            continue
        low, high = TIERS[tier_name]
        if low is not None and high is not None:
            conditions.append(
                and_(
                    Transaction.amount_xmr >= low,
                    Transaction.amount_xmr <= high,
                )
            )
        elif low is not None:
            conditions.append(Transaction.amount_xmr > low)
        elif high is not None:
            conditions.append(Transaction.amount_xmr < high)
        # tier with no bounds shouldn't exist, but skip if it does

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return or_(*conditions)


def build_date_filter(
    start_date: datetime | None, end_date: datetime | None
) -> ColumnElement | None:
    """Build a SQLAlchemy WHERE clause for date range filtering.

    Returns None if neither date is provided.
    """
    conditions: list[ColumnElement] = []
    if start_date is not None:
        conditions.append(Transaction.timestamp >= start_date)
    if end_date is not None:
        conditions.append(Transaction.timestamp <= end_date)
    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return and_(*conditions)


def build_order_by(sort_rules: list[SortRule]) -> list:
    """Build SQLAlchemy order_by clauses from parsed sort rules.

    Returns a default ordering (height desc, timestamp desc) if no rules provided.
    """
    if not sort_rules:
        return [sa_desc(Transaction.height), sa_desc(Transaction.timestamp)]

    clauses = []
    for rule in sort_rules:
        col = SORT_COLUMNS[rule.column]
        if rule.direction == "asc":
            clauses.append(sa_asc(col))
        else:
            clauses.append(sa_desc(col))
    return clauses


def describe_filters(
    start_date: datetime | None,
    end_date: datetime | None,
    tiers: list[str],
    sort_rules: list[SortRule],
) -> dict:
    """Return a human-readable description of the active filters for report metadata."""
    filters: dict = {}

    if start_date or end_date:
        filters["date_range"] = {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None,
        }

    if tiers:
        filters["tiers"] = [
            {"name": t, "range": _tier_description(t)} for t in tiers if t in TIERS
        ]

    if sort_rules:
        filters["sort"] = [
            {"field": r.column, "direction": r.direction} for r in sort_rules
        ]

    return filters


def _tier_description(tier_name: str) -> str:
    """Return a human-readable description of a tier's XMR range."""
    low, high = TIERS.get(tier_name, (None, None))
    if low is not None and high is not None:
        return f"{low} — {high} XMR"
    if low is not None:
        return f"> {low} XMR"
    if high is not None:
        return f"< {high} XMR"
    return "all"
