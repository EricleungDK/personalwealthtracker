from datetime import date
from decimal import Decimal

import personal_wealth_tracker.utils as utils
from personal_wealth_tracker.models import Transaction
from personal_wealth_tracker.utils import normalize_month, parse_danish_decimal, parse_danish_date


def test_parse_danish_decimal():
    assert parse_danish_decimal("1.234,56") == Decimal("1234.56")
    assert parse_danish_decimal("-89,00") == Decimal("-89.00")


def test_parse_danish_date_with_fallback_year():
    assert parse_danish_date("30.04", 2026).isoformat() == "2026-04-30"


def test_normalize_month():
    assert normalize_month("february") == "Feb"
    assert normalize_month("SEP") == "Sep"


def test_transaction_id_scheme_version_is_readable():
    assert hasattr(utils, "TRANSACTION_ID_SCHEME_VERSION")
    assert isinstance(utils.TRANSACTION_ID_SCHEME_VERSION, str)
    assert "stable" in utils.TRANSACTION_ID_SCHEME_VERSION
    assert "v2" in utils.TRANSACTION_ID_SCHEME_VERSION


def test_stable_transaction_ids_do_not_collide_when_fields_contain_delimiters():
    first, second = utils.assign_stable_transaction_ids(
        [
            _transaction(description="A|B", merchant="C"),
            _transaction(description="A", merchant="B|C"),
        ]
    )

    assert first.transaction_id != second.transaction_id


def test_duplicate_like_transaction_ids_survive_adding_another_duplicate_like_transaction():
    first = _transaction(
        description="BAKERY",
        merchant="BAKERY",
        balance=Decimal("800.00"),
        details=("Sender=first",),
    )
    second = _transaction(
        description="BAKERY",
        merchant="BAKERY",
        balance=Decimal("900.00"),
        details=("Sender=second",),
    )
    added = _transaction(
        description="BAKERY",
        merchant="BAKERY",
        balance=Decimal("100.00"),
        details=("Sender=added",),
    )

    original_by_details = {
        transaction.details: transaction.transaction_id
        for transaction in utils.assign_stable_transaction_ids([first, second])
    }
    expanded_by_details = {
        transaction.details: transaction.transaction_id
        for transaction in utils.assign_stable_transaction_ids([added, second, first])
    }

    assert expanded_by_details[first.details] == original_by_details[first.details]
    assert expanded_by_details[second.details] == original_by_details[second.details]
    assert expanded_by_details[added.details] not in set(original_by_details.values())


def test_exact_duplicate_transaction_ids_use_occurrence_suffixes():
    first, second = utils.assign_stable_transaction_ids(
        [
            _transaction(description="BAKERY", merchant="BAKERY"),
            _transaction(description="BAKERY", merchant="BAKERY"),
        ]
    )

    assert first.transaction_id != second.transaction_id
    assert first.transaction_id.endswith(":001")
    assert second.transaction_id.endswith(":002")


def _transaction(
    description: str,
    merchant: str,
    balance: Decimal | None = None,
    details: tuple[str, ...] = (),
) -> Transaction:
    return Transaction(
        transaction_id="",
        date=date(2026, 4, 1),
        interest_date=None,
        description=description,
        amount=Decimal("-10.00"),
        currency="DKK",
        direction="expense",
        balance=balance,
        merchant=merchant,
        details=details,
    )
