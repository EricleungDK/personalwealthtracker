from decimal import Decimal

from personal_wealth_tracker.utils import normalize_month, parse_danish_decimal, parse_danish_date


def test_parse_danish_decimal():
    assert parse_danish_decimal("1.234,56") == Decimal("1234.56")
    assert parse_danish_decimal("-89,00") == Decimal("-89.00")


def test_parse_danish_date_with_fallback_year():
    assert parse_danish_date("30.04", 2026).isoformat() == "2026-04-30"


def test_normalize_month():
    assert normalize_month("february") == "Feb"
    assert normalize_month("SEP") == "Sep"
