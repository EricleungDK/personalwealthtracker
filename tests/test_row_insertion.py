import pytest
from openpyxl import Workbook

from personal_wealth_tracker.row_insertion import evaluate_sheet, shift_formula_rows


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("=D55+D64+D72+D76", "=D55+D65+D73+D77"),
        ("=SUM(D65:D71)", "=SUM(D66:D72)"),
        ("=SUM(D56:D63)", "=SUM(D56:D63)"),
        ("=SUM(D56:D70)", "=SUM(D56:D71)"),
        ("=$D$64+D$80-$D81", "=$D$65+D$81-$D82"),
        ("=SUM($D$52:D52)*-1", "=SUM($D$52:D52)*-1"),
        ("=SUM(D:D)+SUM(60:70)", "=SUM(D:D)+SUM(60:71)"),
        ("='Net worth'!C70+Other!C70", "='Net worth'!C71+Other!C70"),
        ("=IFERROR((E64-D64)/D64,0)", "=IFERROR((E65-D65)/D65,0)"),
        ("=27*20", "=27*20"),
    ],
)
def test_shift_formula_rows_moves_references_at_or_below_insert_row(formula, expected):
    assert (
        shift_formula_rows(formula, formula_sheet="Net worth", target_sheet="Net worth", insert_row=64)
        == expected
    )


def test_shift_formula_rows_from_other_sheet_only_moves_target_sheet_references():
    formula = "='Net worth'!C70+C70"

    assert (
        shift_formula_rows(formula, formula_sheet="Summary", target_sheet="Net worth", insert_row=64)
        == "='Net worth'!C71+C70"
    )


def test_evaluate_sheet_computes_supported_formulas_and_skips_unsupported_ones():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Net worth"
    sheet["C1"] = 10
    sheet["C2"] = 2.5
    sheet["C4"] = "=SUM(C1:C3)"
    sheet["C5"] = "=-0.4*SUM(C1:C2)+C4/2-2^2"
    sheet["C6"] = "=SUM($C$1:C1)*-1"
    sheet["C7"] = "=VLOOKUP(C1,C1:C2,1)"
    sheet["C8"] = "=C7+1"
    sheet["C9"] = "=C1/C3"

    values = evaluate_sheet(workbook, "Net worth")

    assert values[(4, 3)] == 12.5
    assert values[(5, 3)] == pytest.approx(-0.4 * 12.5 + 6.25 - 4)
    assert values[(6, 3)] == -10
    assert (7, 3) not in values
    assert (8, 3) not in values
    assert values[(9, 3)] == "#DIV/0!"
