"""Render the README demo (docs/assets/demo.mp4 + demo.gif) from a real synthetic run.

Runs the real CLI in a temp workspace with synthetic data only, captures its output,
then draws terminal frames with Pillow and encodes them with ffmpeg.

    .venv/bin/python scripts/record_demo.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import openpyxl
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
CLI = [sys.executable, "-m", "personal_wealth_tracker.cli"]

W, H, FPS = 1280, 720, 20
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BG, WIN, BAR = "#010409", "#0d1117", "#161b22"
FG, DIM, GREEN, YELLOW, BLUE, RED = "#e6edf3", "#7d8590", "#3fb950", "#d29922", "#58a6ff", "#f85149"

mono = ImageFont.truetype(FONT, 20)
mono_b = ImageFont.truetype(FONT_BOLD, 20)
small = ImageFont.truetype(FONT, 16)
title_f = ImageFont.truetype(SANS_BOLD, 56)
sub_f = ImageFont.truetype(SANS, 26)
cap_f = ImageFont.truetype(SANS, 22)

LINE_H = 30
X0, Y0 = 70, 110
MAX_LINES = (H - Y0 - 60) // LINE_H


# ---------- real run ----------------------------------------------------------------


def run(cmd: list[str], cwd: Path) -> str:
    env = {"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"}
    out = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, check=True)
    return out.stdout.strip()


def capture() -> dict[str, str]:
    tmp = Path(tempfile.mkdtemp())
    try:
        setup = run(CLI + ["setup", "--workspace", "my-wealth"], tmp)
        ws = tmp / "my-wealth"
        shutil.copy(ws / "examples/synthetic-nordea-transactions.csv", ws / "data/raw_statements")
        shutil.copy(ws / "templates/local-wealth-tracker-template.xlsx", ws / "Net Worth Tracker.xlsx")
        first = run(CLI + ["monthly"], ws)
        sheet = ws / "reports/review_required_2026_apr.xlsx"
        wb = openpyxl.load_workbook(sheet)
        row = [c.value for c in wb["Review Required"][2]]
        wb["Review Required"]["E2"] = row[3]  # accept the suggestion
        wb.save(sheet)
        second = run(CLI + ["monthly"], ws)
        return {"setup": setup, "first": first, "second": second, "row": row}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------- drawing -----------------------------------------------------------------


def colour_for(line: str) -> list[tuple[str, str]]:
    if ":" not in line:
        return [(line, FG)]
    key, val = line.split(":", 1)
    colour = FG
    if key == "Rows in review" and val.strip() != "0":
        colour = YELLOW
    elif key == "Rows in review" or "committed" in val:
        colour = GREEN
    elif key == "Pending amount" and not val.strip().startswith("0.00"):
        colour = YELLOW
    elif key == "Auto rows":
        colour = GREEN
    elif key == "Next action":
        colour = BLUE
    return [(key + ":", DIM), (val, colour)]


def window(title: str = "wealth-tracker — synthetic demo") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((30, 30, W - 30, H - 30), 14, fill=WIN, outline="#30363d")
    d.rounded_rectangle((30, 30, W - 30, 80), 14, fill=BAR)
    d.rectangle((30, 60, W - 30, 80), fill=BAR)
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        d.ellipse((52 + i * 26, 47, 66 + i * 26, 61), fill=c)
    tw = d.textlength(title, font=small)
    d.text(((W - tw) / 2, 45), title, font=small, fill=DIM)
    return img, d


def draw_lines(lines: list[list[tuple[str, str]]], cursor: bool) -> Image.Image:
    img, d = window()
    shown = lines[-MAX_LINES:]
    for i, segs in enumerate(shown):
        x, y = X0, Y0 + i * LINE_H
        for text, colour in segs:
            f = mono_b if colour in (GREEN,) and text.startswith("❯") else mono
            d.text((x, y), text, font=f, fill=colour)
            x += d.textlength(text, font=f)
        if cursor and i == len(shown) - 1:
            d.rectangle((x + 2, y + 3, x + 13, y + 25), fill=FG)
    return img


class Movie:
    def __init__(self) -> None:
        self.frames: list[Image.Image] = []

    def hold(self, img: Image.Image, seconds: float) -> None:
        self.frames.extend([img] * max(1, int(seconds * FPS)))

    def fade(self, a: Image.Image, b: Image.Image, seconds: float = 0.4) -> None:
        n = int(seconds * FPS)
        for i in range(n):
            self.frames.append(Image.blend(a, b, (i + 1) / n))


def prompt(cmd: str) -> list[tuple[str, str]]:
    return [("❯ ", GREEN), (cmd, FG)]


def type_cmd(m: Movie, lines: list, cmd: str, cps: float = 28) -> None:
    lines.append(prompt(""))
    m.hold(draw_lines(lines, True), 0.35)
    step = max(1, int(cps / FPS))
    for i in range(0, len(cmd) + 1, step):
        lines[-1] = prompt(cmd[:i])
        m.hold(draw_lines(lines, True), 1 / FPS)
    lines[-1] = prompt(cmd)
    m.hold(draw_lines(lines, True), 0.3)


def print_out(m: Movie, lines: list, text: str, per_line: float = 0.07) -> None:
    for raw in text.splitlines():
        lines.append(colour_for(raw))
        m.hold(draw_lines(lines, False), per_line)


def comment(lines: list, text: str) -> None:
    lines.append([("# " + text, DIM)])


def card(title: str, sub: str, foot: str = "") -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for f, text, y, c in ((title_f, title, 250, FG), (sub_f, sub, 340, DIM), (cap_f, foot, 420, GREEN)):
        tw = d.textlength(text, font=f)
        d.text(((W - tw) / 2, y), text, font=f, fill=c)
    return img


def sheet(row: list, filled: str) -> Image.Image:
    img, d = window("review_required_2026_apr.xlsx — Exception Sheet")
    cols = [("date", 130), ("description", 230), ("amount", 120), ("suggested_category", 250),
            ("manual_category", 250), ("reason", 200)]
    vals = [row[0], row[1], row[2], row[3], filled, row[5]]
    x, y = 60, 130
    d.text((x, 100), "Only rows the Trust Policy won't auto-accept land here.", font=cap_f, fill=DIM)
    cx = x
    for (name, w), v in zip(cols, vals):
        d.rectangle((cx, y, cx + w, y + 40), fill="#21262d", outline="#30363d")
        d.text((cx + 10, y + 11), name, font=small, fill=DIM)
        active = name == "manual_category"
        d.rectangle((cx, y + 40, cx + w, y + 90), fill="#0f2a1a" if active and filled else WIN,
                    outline=GREEN if active else "#30363d", width=2 if active else 1)
        text = str(v or "")
        while d.textlength(text, font=small) > w - 16:
            text = text[:-2] + "…"
        d.text((cx + 10, y + 55), text, font=small, fill=GREEN if active else FG)
        cx += w
    tips = [("blank", "accept suggestion"), ("NONE", "reject row"), ("category", "override")]
    ty = 300
    for k, v in tips:
        d.text((x, ty), f"{k:>9}", font=mono_b, fill=YELLOW)
        d.text((x + 140, ty), f"→ {v}", font=mono, fill=FG)
        ty += 38
    d.text((x, 470), "Save the sheet, re-run `wealth-tracker monthly`. Decisions are remembered.",
           font=cap_f, fill=DIM)
    return img


# ---------- storyboard --------------------------------------------------------------


def build(out: dict) -> Movie:
    m = Movie()
    intro = card("wealth-tracker", "Bank CSV  →  your Excel net-worth tracker", "100% local · dry-run first · writes only to a copy")
    m.hold(intro, 2.4)

    lines: list = []
    first = draw_lines(lines, True)
    m.fade(intro, first)
    comment(lines, "1. create a workspace (synthetic data only)")
    type_cmd(m, lines, "wealth-tracker setup --workspace my-wealth")
    print_out(m, lines, out["setup"])
    m.hold(draw_lines(lines, False), 1.2)

    lines = []
    comment(lines, "2. drop this month's bank export in, run the month")
    type_cmd(m, lines, "cd my-wealth && cp examples/*.csv data/raw_statements/")
    type_cmd(m, lines, "wealth-tracker monthly")
    print_out(m, lines, out["first"], 0.12)
    before_sheet = draw_lines(lines, False)
    m.hold(before_sheet, 3.0)

    suggestion = out["row"][3]
    empty = sheet(out["row"], "")
    m.fade(before_sheet, empty)
    m.hold(empty, 1.2)
    for i in range(1, len(suggestion) + 1):
        m.hold(sheet(out["row"], suggestion[:i]), 1 / FPS)
    filled = sheet(out["row"], suggestion)
    m.hold(filled, 2.6)

    lines = []
    comment(lines, "3. re-run: nothing left in review → month committed")
    after = draw_lines(lines, True)
    m.fade(filled, after)
    type_cmd(m, lines, "wealth-tracker monthly")
    print_out(m, lines, out["second"], 0.12)
    m.hold(draw_lines(lines, False), 3.5)

    outro = card("Your month, categorised.", "Original workbook untouched · backup + audit trail every run",
                 "github.com/EricleungDK/personalwealthtracker")
    m.fade(draw_lines(lines, False), outro, 0.6)
    m.hold(outro, 2.5)
    return m


def encode(m: Movie) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    frames_dir = Path(tempfile.mkdtemp())
    try:
        for i, f in enumerate(m.frames):
            f.save(frames_dir / f"{i:05d}.png")
        pattern = str(frames_dir / "%05d.png")
        mp4 = ASSETS / "demo.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", pattern,
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart",
                        str(mp4)], check=True)
        gif = ASSETS / "demo.gif"
        vf = "fps=12,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse=dither=none"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4), "-vf", vf, str(gif)], check=True)
    finally:
        shutil.rmtree(frames_dir, ignore_errors=True)


if __name__ == "__main__":
    movie = build(capture())
    encode(movie)
    print(f"{len(movie.frames) / FPS:.1f}s → {ASSETS / 'demo.mp4'}, {ASSETS / 'demo.gif'}")
