from personal_wealth_tracker.nordea_pdf import (
    TextCell,
    _column_anchors,
    _extract_transaction_lines,
    _extract_statement_currency,
    _nearest_column,
    parse_nordea_pdf,
)
import personal_wealth_tracker.utils as utils


def test_extract_transaction_lines_merges_detail_continuations():
    page = [
        TextCell("Dato", 10, 10),
        TextCell("Rentedato", 60, 10),
        TextCell("Detaljer", 120, 10),
        TextCell("Beløb", 300, 10),
        TextCell("Saldo", 380, 10),
        TextCell("30.04", 10, 30),
        TextCell("30.04", 60, 30),
        TextCell("Merchant", 120, 30),
        TextCell("-100,00", 300, 30),
        TextCell("1.000,00", 380, 30),
        TextCell("Extra", 120, 45),
        TextCell("detail", 160, 45),
    ]

    lines = _extract_transaction_lines(page, 2026)

    assert len(lines) == 1
    assert lines[0].date_text == "30.04"
    assert lines[0].amount_text == "-100,00"
    assert "Extra detail" in lines[0].details


def test_column_anchors_from_header_cells():
    anchors = _column_anchors(
        [
            TextCell("Dato", 10, 0),
            TextCell("Rentedato", 60, 0),
            TextCell("Detaljer", 120, 0),
            TextCell("Beløb", 300, 0),
            TextCell("Saldo", 380, 0),
        ]
    )

    assert anchors["details"] == 120


def test_right_aligned_amount_stays_in_amount_column():
    anchors = {
        "date": 51.4,
        "interest_date": 101.0,
        "details": 171.4,
        "amount": 411.8,
        "balance": 490.8,
    }

    assert _nearest_column(454.6, anchors) == "amount"


def test_footer_rows_do_not_extend_last_transaction():
    page = [
        TextCell("Dato", 10, 10),
        TextCell("Rentedato", 60, 10),
        TextCell("Detaljer", 120, 10),
        TextCell("Beløb", 300, 10),
        TextCell("Saldo", 380, 10),
        TextCell("30.04", 10, 30),
        TextCell("30.04", 60, 30),
        TextCell("Merchant", 120, 30),
        TextCell("-100,00", 300, 30),
        TextCell("1.000,00", 380, 30),
        TextCell("Er", 120, 45),
        TextCell("der", 138, 45),
        TextCell("korttransaktioner", 160, 45),
    ]

    lines = _extract_transaction_lines(page, 2026)

    assert len(lines) == 1
    assert lines[0].details == ("Merchant",)


def test_extract_statement_currency_from_pages():
    pages = [[TextCell("Valuta:", 10, 10), TextCell("DKK", 50, 10)]]

    assert _extract_statement_currency(pages) == "DKK"


def test_pdf_transaction_ids_are_stable_across_repeated_parses_order_and_path(
    tmp_path, monkeypatch
):
    rows = [
        ("01.04", "01.04", "NETTO", "-10,00", "990,00"),
        ("02.04", "02.04", "BAKERY", "-20,00", "970,00"),
        ("02.04", "02.04", "BAKERY", "-20,00", "950,00"),
        ("03.04", "03.04", "REFUND SHOP", "100,00", "1050,00"),
    ]

    def pages_for_path(path):
        row_order = [rows[3], rows[1], rows[0], rows[2]] if path.name == "renamed.pdf" else rows
        return [_pdf_page(row_order)]

    monkeypatch.setattr("personal_wealth_tracker.nordea_pdf._extract_pages", pages_for_path)

    original_path = tmp_path / "original.pdf"
    other_path = tmp_path / "same-content-other-path.pdf"
    reordered_path = tmp_path / "renamed.pdf"

    first_parse = parse_nordea_pdf(original_path)
    repeated_parse = parse_nordea_pdf(original_path)
    other_path_parse = parse_nordea_pdf(other_path)
    reordered_parse = parse_nordea_pdf(reordered_path)

    assert [tx.transaction_id for tx in repeated_parse] == [tx.transaction_id for tx in first_parse]
    assert [tx.transaction_id for tx in other_path_parse] == [tx.transaction_id for tx in first_parse]
    assert _ids_by_unique_description(reordered_parse)["NETTO"] == _ids_by_unique_description(first_parse)[
        "NETTO"
    ]
    assert _ids_by_unique_description(reordered_parse)["REFUND SHOP"] == _ids_by_unique_description(
        first_parse
    )["REFUND SHOP"]

    bakery_ids_by_balance = _ids_by_description_and_balance(first_parse, "BAKERY")
    reordered_bakery_ids_by_balance = _ids_by_description_and_balance(reordered_parse, "BAKERY")
    bakery_ids = list(bakery_ids_by_balance.values())
    assert reordered_bakery_ids_by_balance == bakery_ids_by_balance
    assert len(bakery_ids) == 2
    assert len(set(bakery_ids)) == 2
    assert all(
        tx.transaction_id.startswith(f"{utils.TRANSACTION_ID_SCHEME_VERSION}:")
        for tx in first_parse
    )
    assert any(tx.transaction_id.endswith(":001") for tx in first_parse)


def _pdf_page(rows):
    cells = [
        TextCell("Periode:", 10, 1),
        TextCell("01.04.2026", 60, 1),
        TextCell("-", 130, 1),
        TextCell("30.04.2026", 150, 1),
        TextCell("Valuta:", 10, 5),
        TextCell("DKK", 50, 5),
        TextCell("Dato", 10, 10),
        TextCell("Rentedato", 60, 10),
        TextCell("Detaljer", 120, 10),
        TextCell("Beløb", 300, 10),
        TextCell("Saldo", 380, 10),
    ]
    for index, (booked_date, interest_date, description, amount, balance) in enumerate(rows):
        top = 30 + index * 15
        cells.extend(
            [
                TextCell(booked_date, 10, top),
                TextCell(interest_date, 60, top),
                TextCell(description, 120, top),
                TextCell(amount, 300, top),
                TextCell(balance, 380, top),
            ]
        )
    return cells


def _ids_by_unique_description(transactions):
    return {
        transaction.description: transaction.transaction_id
        for transaction in transactions
        if sum(1 for item in transactions if item.description == transaction.description) == 1
    }


def _ids_by_description_and_balance(transactions, description):
    return {
        transaction.balance: transaction.transaction_id
        for transaction in transactions
        if transaction.description == description
    }
