from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from personal_wealth_tracker.models import Transaction
from personal_wealth_tracker.outbound_redaction import (
    OutboundRow,
    amount_band,
    describe_outbound,
    redact_for_hosted_judgment,
    redact_merchant,
)


def _tx(description: str, amount: str = "-120.50", direction: str = "debit") -> Transaction:
    return Transaction(
        transaction_id="tx-1",
        date=date(2026, 8, 3),
        interest_date=None,
        description=description,
        amount=Decimal(amount),
        currency="DKK",
        direction=direction,
        balance=Decimal("12345.67"),
        merchant=description,
        account_name="Main account 1234 5678901234",
        source_file=Path("secret.csv"),
        details=("Sender=1234 5678901234", "Recipient=9876 1234567890", "Balance=12345.67"),
    )


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Netto Osterbro 4102", "NETTO OSTERBRO"),
        ("Café Ømme", "CAFE MME"),  # NFKD ascii fold, same as normalize_text
        ("Reg 1234 5678901234 overfoersel", "REG <ID> OVERFOERSEL"),
        ("DK5000400440116243 payment", "<ID> PAYMENT"),
        ("Ring +45 12345678", "RING <NUM>"),
        ("Ring 12 34 56 78", "RING <NUM>"),
        ("Card 541234XXXXXX1234 purchase", "CARD <NUM> PURCHASE"),
        ("Order 987654321 shop", "ORDER <NUM> SHOP"),
        ("Foreign transfer 7464016320200826S103", "FOREIGN TRANSFER <ID>"),
        ("REMA1000 Hadsten", "REMA1000 HADSTEN"),  # brand digits stay
        ("Shop 12345 west", "SHOP WEST"),
        ("Ref 123456 x", "REF <ID> X"),  # short store numbers drop, like the memory key
        ("mail me@example.com refund", "MAIL <EMAIL> REFUND"),
        ("MobilePay Anna Hansen", "MOBILEPAY <PERSON>"),
        ("MOBILEPAY", "MOBILEPAY"),
        ("Overførsel Peter Jensen", "OVERFRSEL <PERSON>"),
        ("Straksoverførsel Peter", "STRAKSOVERFRSEL <PERSON>"),
        ("Transfer Some Body", "TRANSFER <PERSON>"),
        ("Betaling Ole Olsen", "BETALING <PERSON>"),
    ],
)
def test_redact_merchant(raw, expected):
    assert redact_merchant(raw) == expected


def test_redact_merchant_blocklist_masks_known_private_names():
    assert redact_merchant("Kim Larsen rent", blocklist=["kim larsen"]) == "<PERSON> RENT"


@pytest.mark.parametrize(
    "amount, band",
    [("-45", "<100"), ("-100", "100-500"), ("499.99", "100-500"), ("-500", "500-2000"),
     ("-1999", "500-2000"), ("2000", "2000-10000"), ("-9999.99", "2000-10000"), ("10000", ">10000")],
)
def test_amount_band(amount, band):
    assert amount_band(Decimal(amount)) == band


def test_redact_for_hosted_judgment_exposes_only_three_fields():
    row = redact_for_hosted_judgment(_tx("MobilePay Anna Hansen 12345678", "-350"))
    assert row == OutboundRow(merchant="MOBILEPAY <PERSON>", amount_band="100-500", direction="debit")
    assert set(OutboundRow.__dataclass_fields__) == {"merchant", "amount_band", "direction"}
    payload = repr(row) + str(row.as_state())
    for secret in ("1234", "5678901234", "12345.67", "secret.csv", "2026", "tx-1", "Main account"):
        assert secret not in payload


def test_as_state_keys_are_stable():
    row = redact_for_hosted_judgment(_tx("Netto", "800", "credit"))
    assert row.as_state() == {"merchant": "NETTO", "amount_band_dkk": "500-2000", "direction": "credit"}


def test_describe_outbound_is_a_readable_table():
    rows = [redact_for_hosted_judgment(_tx("Netto 4102")), redact_for_hosted_judgment(_tx("MobilePay Bo", "-20"))]
    text = describe_outbound(rows)
    assert "NETTO" in text and "MOBILEPAY <PERSON>" in text
    assert "4102" not in text and "Bo" not in text
    assert text.splitlines()[0].startswith("merchant")


def test_hosted_payload_never_carries_the_raw_merchant_the_local_prompt_shows():
    raw = "7-ELEVEN 7060 Paleet"
    payload = str(redact_for_hosted_judgment(_tx(raw)).as_state())
    assert "PALEET" in payload
    for secret in (raw, "7060", "Paleet"):
        assert secret not in payload
