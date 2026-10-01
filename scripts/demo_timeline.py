"""Pure pieces of the README demo: what settled each row, labels, and media budgets.

Kept free of I/O so `scripts/record_demo.py` stays a thin, reproducible driver.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MIN_SECONDS, MAX_SECONDS = 15, 30
MIN_FPS, MAX_FPS = 15, 25
MAX_GIF_BYTES = 5_000_000

SETTLERS = {"rule": "rules", "category_memory": "memory"}


@dataclass(frozen=True)
class SettledRow:
    description: str
    amount: str
    category: str
    how: str
    held: bool


def _settler(method: str) -> str:
    if method.startswith("local_llm"):
        return "consensus"
    return SETTLERS.get(method, method)


def _short_reason(reason: str) -> str:
    if reason.endswith("is a never-auto category."):
        return "never-auto"
    cap = re.search(r"above the auto cap (\S+)\.$", reason)
    if cap:
        return f"over {cap.group(1)} cap"
    return reason.rstrip(".")


def settle_rows(rows: list[dict], held_reasons: dict[str, str]) -> list[SettledRow]:
    """Rows of `categorized_transactions_*.csv`; held rows need the trust-policy reason."""
    settled = []
    for item in rows:
        held = item["review_required"] == "True"
        if held:
            reason = held_reasons.get(item["transaction_id"])
            if reason is None:
                raise ValueError(f"No trust-policy reason for held row {item['transaction_id']}")
            how = f"held: {_short_reason(reason)}"
        else:
            how = _settler(item["method"])
        settled.append(
            SettledRow(item["description"], item["amount"], item["category"], how, held)
        )
    return settled


def summary(settled: list[SettledRow]) -> str:
    counts = dict.fromkeys(("rules", "memory", "consensus"), 0)
    for item in settled:
        if not item.held:
            counts[item.how] += 1
    parts = [f"{name} {n}" for name, n in counts.items() if n]
    parts.append(f"held for you {sum(item.held for item in settled)}")
    return " · ".join(parts)


def model_wait_label(seconds: float, models: list[str]) -> str:
    return f"local consensus, {len(models)} models · {seconds:.0f} s wait cut"


def check_duration(seconds: float) -> None:
    if not MIN_SECONDS <= seconds <= MAX_SECONDS:
        raise ValueError(f"Demo is {seconds:.1f} s; README budget is 15–30 s.")


def check_media(gif_bytes: int, fps: int) -> None:
    if gif_bytes >= MAX_GIF_BYTES:
        raise ValueError(f"GIF is {gif_bytes} bytes; must stay under 5 MB.")
    if not MIN_FPS <= fps <= MAX_FPS:
        raise ValueError(f"GIF runs at {fps} fps; must be 15–25 fps.")


def recording_record(
    *,
    revision: str,
    recorded: str,
    width: int,
    height: int,
    capture_scale: int,
    fps: int,
    duration: float,
    waits: list[float],
    models: list[str],
    files: dict[str, str],
) -> dict:
    return {
        "source_revision": revision,
        "recorded": recorded,
        "data": "synthetic",
        "width": width,
        "height": height,
        "capture_scale": capture_scale,
        "fps": fps,
        "duration_seconds": round(duration, 1),
        "model_waits_cut_seconds": waits,
        "models": models,
        "files": files,
        "script": "scripts/record_demo.py",
    }
