from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "nordea_account_statement.redacted.pdf"


def main() -> None:
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_bytes(_build_pdf())
    print(f"Wrote {FIXTURE_PATH}")


def _build_pdf() -> bytes:
    content = _content_stream()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream",
    ]

    output = bytearray(b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(output)


def _content_stream() -> bytes:
    entries = [
        (50, 760, 16, "Kontoudskrift"),
        (50, 735, 10, "Periode: 01.04.2026 - 30.04.2026"),
        (50, 720, 10, "Valuta: DKK"),
        (50, 705, 10, "Dato"),
        (100, 705, 10, "Rentedato"),
        (170, 705, 10, "Detaljer"),
        (410, 705, 10, "Beloeb"),
        (490, 705, 10, "Saldo"),
        (50, 675, 10, "30.04"),
        (100, 675, 10, "30.04"),
        (170, 675, 10, "REDACTED APPLE.COM/BILL"),
        (455, 675, 10, "-25,00"),
        (505, 675, 10, "9.975,00"),
        (50, 645, 10, "29.04"),
        (100, 645, 10, "29.04"),
        (170, 645, 10, "REDACTED SALARY"),
        (438, 645, 10, "10.000,00"),
        (505, 645, 10, "19.975,00"),
        (50, 615, 10, "28.04"),
        (100, 615, 10, "28.04"),
        (170, 615, 10, "REDACTED FOREIGN CARD"),
        (455, 615, 10, "-86,10"),
        (505, 615, 10, "19.888,90"),
        (170, 600, 10, "6,9700 NOK 123,45"),
        (170, 565, 10, "Er der korttransaktioner paa din konto, skal du goere indsigelse."),
    ]

    lines = ["BT"]
    for x, y, size, text in entries:
        lines.append(f"/F1 {size} Tf")
        lines.append(f"1 0 0 1 {x} {y} Tm ({_escape_pdf_text(text)}) Tj")
    lines.append("ET")
    return "\n".join(lines).encode("ascii")


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


if __name__ == "__main__":
    main()
