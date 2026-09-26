"""Allowlist redaction for anything sent to a hosted judgment service.

Only three fields ever leave the machine: a redacted merchant string, a coarse
amount band and the direction. Dates, accounts, balances, ids and raw lines are
never exposed by this module's interface.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from .models import Transaction
from .utils import normalize_text

_EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
_IBAN = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")
_REG_ACCOUNT = re.compile(r"\b\d{4}[ -]?\d{6,10}\b")
_REFERENCE = re.compile(r"\b(?=[A-Z0-9]*\d{6})[A-Z0-9]{6,}\b")
_PHONE = re.compile(r"(?:\+?45[ -]?)?\b\d{2}(?: ?\d{2}){3}\b")
_MASKED_CARD = re.compile(r"\b(?=[\dX*]*\d{4})[\dX*]{8,19}\b")
_SHORT_NUMBER = re.compile(r"\b\d+\b")
_TRANSFER_PREFIX = re.compile(
    r"^(MOBILEPAY|(?:STRAKS)?OVERF(?:OE|O)?RSEL|TRANSFER|BETALING)\b\s*(.*)$"
)
_BANDS = ((100, "<100"), (500, "100-500"), (2000, "500-2000"), (10000, "2000-10000"))


def redact_merchant(text: str, blocklist: Iterable[str] = ()) -> str:
    out = _EMAIL.sub("<EMAIL>", text)
    out = normalize_text(out)
    out = _IBAN.sub("<ID>", out)
    out = _REG_ACCOUNT.sub("<ID>", out)
    out = _PHONE.sub("<NUM>", out)
    out = _MASKED_CARD.sub("<NUM>", out)
    out = _REFERENCE.sub("<ID>", out)
    out = _SHORT_NUMBER.sub(" ", out)
    for name in blocklist:
        needle = normalize_text(name)
        if needle:
            out = re.sub(r"\b" + re.escape(needle) + r"\b", "<PERSON>", out)
    out = re.sub(r"\s+", " ", out).strip()
    match = _TRANSFER_PREFIX.match(out)
    if match and match.group(2).strip():
        return f"{match.group(1)} <PERSON>"
    return out


def amount_band(amount: Decimal) -> str:
    value = abs(amount)
    for limit, label in _BANDS:
        if value < limit:
            return label
    return ">10000"


@dataclass(frozen=True)
class OutboundRow:
    merchant: str
    amount_band: str
    direction: str

    def as_state(self) -> dict[str, str]:
        return {"merchant": self.merchant, "amount_band_dkk": self.amount_band, "direction": self.direction}


def redact_for_hosted_judgment(transaction: Transaction, blocklist: Iterable[str] = ()) -> OutboundRow:
    return OutboundRow(
        merchant=redact_merchant(transaction.description, blocklist),
        amount_band=amount_band(transaction.amount),
        direction=transaction.direction,
    )


def describe_outbound(rows: Iterable[OutboundRow]) -> str:
    rows = list(rows)
    width = max([len("merchant")] + [len(r.merchant) for r in rows])
    lines = [f"{'merchant'.ljust(width)}  band        direction"]
    lines += [f"{r.merchant.ljust(width)}  {r.amount_band.ljust(10)}  {r.direction}" for r in rows]
    return "\n".join(lines)
