from personal_wealth_tracker.nordea_pdf import (
    TextCell,
    _column_anchors,
    _extract_transaction_lines,
    _nearest_column,
)


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
