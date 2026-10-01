"""Render the README demo from a real synthetic run.

Runs the real CLI in a temp workspace on synthetic data only, with the local Ollama
models, then draws terminal and Exception Sheet frames at 2x with Pillow and scales them
down with ffmpeg. Model waits are cut and labelled with their measured length.

    .venv/bin/python scripts/record_demo.py [--models gemma4:e4b gemma4:12b]

Writes docs/assets/demo.{gif,mp4,webm}, demo-poster.png and demo-recording.json.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import openpyxl
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import demo_timeline as timeline

from personal_wealth_tracker.config import load_config
from personal_wealth_tracker.trust_policy import Evidence, RowFacts, decide_authority

ASSETS = ROOT / "docs" / "assets"
CLI = [sys.executable, "-m", "personal_wealth_tracker.cli"]
OLLAMA = "http://localhost:11434"

W, H, SCALE = 1280, 720, 2  # logical size; frames are drawn at SCALE times, then scaled down
FPS, GIF_FPS = 20, 15
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BG, WIN, BAR, LINE = "#010409", "#0d1117", "#161b22", "#30363d"
FG, DIM, GREEN, YELLOW, BLUE, PURPLE = (
    "#e6edf3", "#7d8590", "#3fb950", "#d29922", "#58a6ff", "#bc8cff")
HOW_COLOUR = {"rules": BLUE, "memory": PURPLE, "consensus": GREEN}

STATEMENT = """﻿Booking date;Amount;Balance;Currency;Name;Title;Sender;Recipient;Reconciled
2026/04/01;25000,00;25000,00;DKK;SYNTHETIC EMPLOYER;Synthetic payroll;;;Yes
2026/04/03;-299,00;24701,00;DKK;SYNTHETIC FIBER NET;Synthetic internet;;;Yes
2026/04/05;-450,25;24251,00;DKK;SYNTHETIC GROCER;Synthetic groceries;;;Yes
2026/04/07;-320,00;23931,00;DKK;METRO TRANSIT CARD;Monthly transit pass;;;Yes
2026/04/08;-149,00;23782,00;DKK;SYNTHETIC TELECOM;Synthetic phone;;;Yes
2026/04/12;-79,00;23703,00;DKK;CLOUD STORAGE SUBSCRIPTION;Monthly cloud storage;;;Yes
2026/04/20;-1450,00;22253,00;DKK;SYNTHETIC HOME INSURANCE;Quarterly home insurance;;;Yes
"""
# One decision from a prior synthetic month, so Category Memory has something to recall.
PRIOR_DECISION = (
    "transaction_id,date,description,amount,direction,confirmed_category,confirmed\n"
    "synthetic-2026-03,2026-03-03,SYNTHETIC FIBER NET,-299.00,expense,Internet (monthly),yes\n"
)
STATEMENT_NAME = "synthetic-nordea-2026-04.csv"
PICK = "SYNTHETIC HOME INSURANCE"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size * SCALE)


mono, mono_b, small = font(FONT, 24), font(FONT_BOLD, 24), font(FONT, 16)
table_f, cell_f = font(FONT, 22), font(FONT, 20)
title_f, sub_f, cap_f = font(SANS_BOLD, 56), font(SANS, 26), font(SANS, 22)
LINE_H, X0, Y0 = 38, 64, 112
MAX_LINES = (H - Y0 - 60) // LINE_H


def px(*values: float) -> tuple[int, ...]:
    return tuple(int(v * SCALE) for v in values)


# ---------- real run ----------------------------------------------------------------


def run(cmd: list[str], cwd: Path) -> tuple[str, float]:
    env = {"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"}
    start = time.monotonic()
    out = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, check=True)
    return out.stdout.strip(), time.monotonic() - start


def ready_models(models: list[str]) -> None:
    with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5) as response:
        installed = {m["name"] for m in json.load(response)["models"]}
    missing = [m for m in models if m not in installed]
    if missing:
        raise SystemExit(f"Ollama is missing {missing}; pull them or pass --models.")
    for model in models:  # load now, so the labelled wait is inference rather than a cold start
        body = json.dumps({"model": model, "keep_alive": "30m"}).encode()
        request = urllib.request.Request(f"{OLLAMA}/api/generate", body,
                                         {"Content-Type": "application/json"})
        urllib.request.urlopen(request, timeout=600).read()


def use_models(settings: Path, models: list[str]) -> None:
    keys = {"  model:": models[0], "  second_model:": models[1]}
    lines = [next((f'{k} "{v}"' for k, v in keys.items() if line.startswith(k)), line)
             for line in settings.read_text(encoding="utf-8").splitlines()]
    settings.write_text("\n".join(lines) + "\n", encoding="utf-8")


def held_reasons(ws: Path, rows: list[dict]) -> dict[str, str]:
    """The real trust policy's reason for each held row."""
    policy = load_config(ws / "config").trust_policy
    return {
        r["transaction_id"]: decide_authority(
            Evidence(tier=r["method"], category=r["category"], confidence=float(r["confidence"])),
            RowFacts(amount=Decimal(r["amount"])),
            policy,
        ).reason
        for r in rows
        if r["review_required"] == "True"
    }


def decide(sheet_path: Path) -> tuple[list[list], list[str], str]:
    """Blank accepts the payroll suggestion; the insurance row gets a dropdown pick.

    Returns the sheet as shown, the pick's real dropdown window, and the pick.
    """
    wb = openpyxl.load_workbook(sheet_path)
    ws = wb["Review Required"]
    header = [c.value for c in ws[1]]
    rows = [[c.value for c in r] for r in ws.iter_rows(min_row=2)]
    for i, row in enumerate(rows, start=2):
        if row[header.index("description")] == PICK:
            pick = row[header.index("suggested_category")]
            cell = ws.cell(i, header.index("manual_category") + 1)
            cell.value = pick
            listed = next(v for v in ws.data_validations.dataValidation
                          if cell.coordinate in v.sqref)
            column = re.search(r"!\$([A-Z]+)\$", listed.formula1).group(1)
            options = [c.value for c in wb["Decision Options"][column] if c.value]
    wb.save(sheet_path)
    at = options.index(pick)
    return [header, *rows], options[at - 1:at + 2], pick


@dataclass(frozen=True)
class Run:
    """What the real run produced; the storyboard draws only from this."""

    setup: str
    first: str
    second: str
    settled: list[timeline.SettledRow]
    sheet: list[list]
    options: list[str]
    pick: str
    backups: list[str]
    waits: tuple[float, float]


def workspace(tmp: Path, models: list[str]) -> tuple[Path, str]:
    """A fresh synthetic workspace: one remembered decision, April's export dropped in."""
    setup, _ = run(CLI + ["setup", "--workspace", "my-wealth"], tmp)
    ws = tmp / "my-wealth"
    use_models(ws / "config" / "settings.yaml", models)
    (tmp / "prior.csv").write_text(PRIOR_DECISION, encoding="utf-8")
    run(CLI + ["learn-category-memory", "--decisions", str(tmp / "prior.csv")], ws)
    (ws / "data" / "raw_statements" / STATEMENT_NAME).write_text(STATEMENT, encoding="utf-8")
    return ws, setup


def capture(models: list[str]) -> Run:
    tmp = Path(tempfile.mkdtemp())
    try:
        ws, setup = workspace(tmp, models)
        first, first_wait = run(CLI + ["monthly"], ws)
        with open(ws / "reports" / "categorized_transactions_2026_apr.csv", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        settled = timeline.settle_rows(rows, held_reasons(ws, rows))
        if not any(r.how == "consensus" for r in settled):
            raise SystemExit("No row settled by local consensus; check the models.")
        sheet, options, pick = decide(ws / "reports" / "review_required_2026_apr.xlsx")
        second, second_wait = run(CLI + ["monthly"], ws)
        if "month committed" not in second:
            raise SystemExit(f"Re-run did not commit:\n{second}")
        backups = sorted(p.name for p in (ws / "data" / "backups").iterdir())
        return Run(setup, first, second, settled, sheet, options, pick, backups,
                   (first_wait, second_wait))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------- drawing (coordinates are logical; px() scales them) -----------------------


def colour_for(line: str) -> list[tuple[str, str]]:
    if ":" not in line:
        return [(line, FG)]
    key, val = line.split(":", 1)
    colour = FG
    if key == "Rows in review":
        colour = YELLOW if val.strip() != "0" else GREEN
    elif key == "Auto rows":
        colour = GREEN
    elif key == "Next action":
        colour = GREEN if "committed" in val else BLUE
    return [(key + ":", DIM), (val, colour)]


def window(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", px(W, H), BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(px(30, 30, W - 30, H - 30), 14 * SCALE, fill=WIN, outline=LINE, width=SCALE)
    d.rounded_rectangle(px(30, 30, W - 30, 80), 14 * SCALE, fill=BAR)
    d.rectangle(px(30, 60, W - 30, 80), fill=BAR)
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        d.ellipse(px(52 + i * 26, 47, 66 + i * 26, 61), fill=c)
    tw = d.textlength(title, font=small) / SCALE
    d.text(px((W - tw) / 2, 45), title, font=small, fill=DIM)
    return img, d


def terminal(lines: list, cursor: bool) -> Image.Image:
    img, d = window("wealth-tracker — synthetic demo")
    shown = lines[-MAX_LINES:]
    for i, segs in enumerate(shown):
        x, y = X0, Y0 + i * LINE_H
        for text, colour in segs:
            face = mono_b if text.startswith("❯") else mono
            d.text(px(x, y), text, font=face, fill=colour)
            x += d.textlength(text, font=face) / SCALE
        if cursor and i == len(shown) - 1:
            d.rectangle(px(x + 2, y + 3, x + 15, y + 30), fill=FG)
    return img


def card(title: str, sub: str, foot: str) -> Image.Image:
    img = Image.new("RGB", px(W, H), BG)
    d = ImageDraw.Draw(img)
    for face, text, y, c in ((title_f, title, 250, FG), (sub_f, sub, 340, DIM), (cap_f, foot, 420, GREEN)):
        tw = d.textlength(text, font=face) / SCALE
        d.text(px((W - tw) / 2, y), text, font=face, fill=c)
    return img


def fit(d: ImageDraw.ImageDraw, text: str, face, width: float) -> str:
    while d.textlength(text, font=face) / SCALE > width and len(text) > 1:
        text = text[:-2] + "…"
    return text


def settled_view(settled: list, shown: int) -> Image.Image:
    img, d = window("How April settled — reports/categorized_transactions_2026_apr.csv")
    cols = [("transaction", 380), ("amount", 130), ("category", 320), ("settled by", 280)]
    x0, y = 84, 108
    x = x0
    for name, w in cols:
        d.text(px(x, y), name, font=small, fill=DIM)
        x += w
    d.line(px(x0, y + 30, W - 80, y + 30), fill=LINE, width=SCALE)
    for i, row in enumerate(settled[:shown]):
        ry = y + 50 + i * 58
        if row.held:
            d.rounded_rectangle(px(x0 - 16, ry - 12, W - 68, ry + 42), 8 * SCALE, fill="#2b2111")
        colour = YELLOW if row.held else HOW_COLOUR[row.how]
        x = x0
        for (name, w), text in zip(cols, (row.description, row.amount, row.category, row.how)):
            d.text(px(x, ry), fit(d, text, table_f, w - 12), font=table_f,
                   fill=colour if name == "settled by" else FG)
            x += w
    if shown == len(settled):
        d.text(px(x0, H - 104), timeline.summary(settled), font=sub_f, fill=GREEN)
    return img


def sheet_view(sheet: list[list], picked: str, dropdown: list[str] | None, highlight: int) -> Image.Image:
    img, d = window("reports/review_required_2026_apr.xlsx — Exception Sheet")
    header, rows = sheet[0], sheet[1:]
    show = [("description", 350), ("amount", 150), ("suggested_category", 300), ("manual_category", 340)]
    x0, y = 70, 160
    d.text(px(x0, 108), "Only rows the trust policy won't auto-accept land here.", font=cap_f, fill=DIM)
    x = x0
    for name, w in show:
        d.rectangle(px(x, y, x + w, y + 44), fill="#21262d", outline=LINE, width=SCALE)
        d.text(px(x + 12, y + 11), name, font=cell_f, fill=DIM)
        x += w
    for r, row in enumerate(rows):
        ry = y + 44 + r * 56
        x = x0
        for name, w in show:
            active = name == "manual_category"
            is_pick = active and row[header.index("description")] == PICK
            value = picked if is_pick else str(row[header.index(name)] or "")
            d.rectangle(px(x, ry, x + w, ry + 56), fill="#0f2a1a" if is_pick and picked else WIN,
                        outline=GREEN if is_pick else LINE, width=2 * SCALE if is_pick else SCALE)
            if active and not value:
                d.text(px(x + 12, ry + 16), "blank → accept", font=cell_f, fill=DIM)
            else:
                d.text(px(x + 12, ry + 16), fit(d, value, cell_f, w - 20), font=cell_f,
                       fill=GREEN if active else FG)
            if is_pick and dropdown is not None:
                d.text(px(x + w - 30, ry + 16), "▾", font=cell_f, fill=GREEN)
                for i, option in enumerate(dropdown):
                    oy = ry + 56 + i * 40
                    d.rectangle(px(x, oy, x + w, oy + 40), fill="#1f6feb" if i == highlight else BAR,
                                outline=LINE, width=SCALE)
                    d.text(px(x + 12, oy + 8), option, font=cell_f, fill=FG)
            x += w
    ty = 440
    for key, value in (("blank", "accept"), ("NONE", "reject"), ("dropdown", "pick a category")):
        d.text(px(x0, ty), f"{key:>9}", font=mono_b, fill=YELLOW)
        d.text(px(x0 + 170, ty), f"→ {value}", font=mono, fill=FG)
        ty += 46
    return img


class Movie:
    """Unique frames with hold durations; hard cuts keep the GIF small."""

    def __init__(self) -> None:
        self.shots: list[tuple[Image.Image, float]] = []

    @property
    def seconds(self) -> float:
        return sum(t for _, t in self.shots)

    def hold(self, img: Image.Image, seconds: float) -> None:
        self.shots.append((img, max(1, round(seconds * FPS)) / FPS))



def prompt(cmd: str) -> list[tuple[str, str]]:
    return [("❯ ", GREEN), (cmd, FG)]


def type_cmd(m: Movie, lines: list, cmd: str, chars_per_frame: int = 2) -> None:
    lines.append(prompt(""))
    m.hold(terminal(lines, True), 0.25)
    for i in range(0, len(cmd) + 1, chars_per_frame):
        lines[-1] = prompt(cmd[:i])
        m.hold(terminal(lines, True), 1 / FPS)
    lines[-1] = prompt(cmd)
    m.hold(terminal(lines, True), 0.2)


def print_out(m: Movie, lines: list, text: str, per_line: float = 0.08) -> None:
    for raw in text.splitlines():
        lines.append(colour_for(raw))
        m.hold(terminal(lines, False), per_line)


def wait_cut(m: Movie, lines: list, seconds: float, models: list[str]) -> None:
    lines.append([("… " + timeline.model_wait_label(seconds, models), YELLOW)])
    m.hold(terminal(lines, False), 1.0)


def keep_lines(text: str, keys: tuple[str, ...]) -> str:
    return "\n".join(line for line in text.splitlines() if line.split(":", 1)[0] in keys)


# ---------- storyboard --------------------------------------------------------------


def build(out: Run, models: list[str]) -> Movie:
    m = Movie()
    intro = card("Personal Wealth Tracker", "Bank CSV  →  your Excel net-worth workbook",
                 "local-first · synthetic data")
    m.hold(intro, 1.6)

    lines: list = []
    type_cmd(m, lines, "wealth-tracker setup --workspace my-wealth", 3)
    print_out(m, lines, keep_lines(out.setup, ("Workspace", "Files written")), 0.1)
    type_cmd(m, lines, f"cd my-wealth && cp ~/{STATEMENT_NAME} data/raw_statements/", 4)
    type_cmd(m, lines, "wealth-tracker monthly")
    wait_cut(m, lines, out.waits[0], models)
    print_out(m, lines, keep_lines(out.first, (
        "Month", "Auto rows", "Rows in review", "Exception sheet")), 0.12)
    before = terminal(lines, False)
    m.hold(before, 1.6)

    settled = out.settled
    m.hold(settled_view(settled, 0), 0.3)
    for n in range(1, len(settled) + 1):
        m.hold(settled_view(settled, n), 0.22)
    done = settled_view(settled, len(settled))
    m.hold(done, 2.4)

    sheet = out.sheet
    options = out.options
    empty = sheet_view(sheet, "", None, -1)
    m.hold(empty, 0.9)
    for step in (-1, 0, 1):
        m.hold(sheet_view(sheet, "", options, step), 0.35)
    filled = sheet_view(sheet, out.pick, None, -1)
    m.hold(filled, 1.8)

    lines = [[("# re-run: nothing left in review → month committed", DIM)]]
    type_cmd(m, lines, "wealth-tracker monthly")
    wait_cut(m, lines, out.waits[1], models)
    print_out(m, lines, keep_lines(out.second, (
        "Auto rows", "Rows in review", "Output workbook", "Next action")), 0.12)
    type_cmd(m, lines, "ls data/backups", 3)
    print_out(m, lines, "\n".join(out.backups), 0.1)
    end = terminal(lines, False)
    m.hold(end, 2.2)

    outro = card("Month committed in place.", "Backup kept · Category Memory learned · audit trail",
                 "github.com/EricleungDK/personalwealthtracker")
    m.hold(outro, 1.6)
    return m


# ---------- encoding ----------------------------------------------------------------


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def encode(m: Movie) -> dict[str, str]:
    ASSETS.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp())
    try:
        concat, saved = [], {}
        for img, seconds in m.shots:
            if id(img) not in saved:
                saved[id(img)] = work / f"{len(saved):05d}.png"
                img.save(saved[id(img)])
            concat.append(f"file '{saved[id(img)]}'\nduration {seconds:.4f}")
        concat.append(f"file '{saved[id(m.shots[-1][0])]}'")
        (work / "shots.txt").write_text("\n".join(concat) + "\n", encoding="utf-8")
        source = ["-f", "concat", "-safe", "0", "-i", str(work / "shots.txt")]
        down = f"fps={FPS},scale={W}:{H}:flags=lanczos"
        ffmpeg(*source, "-vf", down, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
               "-movflags", "+faststart", str(ASSETS / "demo.mp4"))
        ffmpeg(*source, "-vf", down, "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "42",
               "-deadline", "good", "-cpu-used", "1", "-row-mt", "1", str(ASSETS / "demo.webm"))
        gif = (f"fps={GIF_FPS},scale={W}:{H}:flags=lanczos,split[a][b];"
               "[a]palettegen=max_colors=128:stats_mode=diff[p];"
               "[b][p]paletteuse=dither=none:diff_mode=rectangle")
        ffmpeg(*source, "-vf", gif, str(ASSETS / "demo.gif"))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return {"gif": "demo.gif", "mp4": "demo.mp4", "webm": "demo.webm", "poster": "demo-poster.png"}


def revision() -> str:
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()

    dirty = git("status", "--porcelain", "--", "scripts", "src")
    return git("rev-parse", "HEAD") + ("-dirty" if dirty else "")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--models", nargs=2, default=["gemma4:e4b", "gemma4:12b"])
    models = parser.parse_args().models
    ready_models(models)
    out = capture(models)
    movie = build(out, models)
    timeline.check_duration(movie.seconds)
    files = encode(movie)
    poster = settled_view(out.settled, len(out.settled))
    poster.resize((W, H), Image.LANCZOS).save(ASSETS / "demo-poster.png", optimize=True)
    timeline.check_media((ASSETS / "demo.gif").stat().st_size, GIF_FPS)
    record = timeline.recording_record(
        revision=revision(), recorded=dt.datetime.now().astimezone().date().isoformat(), width=W, height=H,
        capture_scale=SCALE, fps=FPS, duration=movie.seconds,
        waits=[round(w, 1) for w in out.waits], models=models, files=files)
    (ASSETS / "demo-recording.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
