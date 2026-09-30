import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "demo_timeline.py"
spec = importlib.util.spec_from_file_location("demo_timeline", SCRIPT)
demo = importlib.util.module_from_spec(spec)
sys.modules["demo_timeline"] = demo
spec.loader.exec_module(demo)


def row(tid, description, amount, category, method, review):
    return {
        "transaction_id": tid,
        "description": description,
        "amount": amount,
        "category": category,
        "method": method,
        "review_required": review,
    }


ROWS = [
    row("t1", "SYNTHETIC EMPLOYER", "25000.00", "Full-time job (net)", "rule", "True"),
    row("t2", "SYNTHETIC FIBER NET", "-299.00", "Internet (monthly)", "category_memory", "False"),
    row("t3", "METRO TRANSIT CARD", "-320.00", "Transportation", "local_llm_gemma", "False"),
    row("t4", "SYNTHETIC HOME INSURANCE", "-1450.00", "Insurance (monthly)", "local_llm_gemma", "True"),
]
HELD = {
    "t1": "Full-time job (net) is a never-auto category.",
    "t4": "Amount 1450.00 is above the auto cap 1000.",
}


def test_each_row_says_what_settled_it():
    settled = demo.settle_rows(ROWS, HELD)

    assert [s.how for s in settled] == [
        "held: never-auto",
        "memory",
        "consensus",
        "held: over 1000 cap",
    ]
    assert [s.held for s in settled] == [True, False, False, True]
    assert settled[3].description == "SYNTHETIC HOME INSURANCE"
    assert settled[3].amount == "-1450.00"


def test_held_row_without_policy_reason_is_an_error():
    with pytest.raises(ValueError, match="t4"):
        demo.settle_rows(ROWS, {"t1": HELD["t1"]})


def test_summary_counts_settlers_and_exceptions():
    summary = demo.summary(demo.settle_rows(ROWS, HELD))

    assert summary == "memory 1 · consensus 1 · held for you 2"


def test_summary_orders_rule_first_and_skips_zero():
    rows = ROWS + [row("t5", "SYNTHETIC GROCER", "-450.25", "Groceries (monthly)", "rule", "False")]

    assert demo.summary(demo.settle_rows(rows, HELD)) == (
        "rules 1 · memory 1 · consensus 1 · held for you 2"
    )


def test_model_wait_label_names_models_and_real_duration():
    label = demo.model_wait_label(51.3, ["gemma4:e4b", "gemma4:12b"])

    assert label == "local models gemma4:e4b + gemma4:12b · 51 s wait cut"


@pytest.mark.parametrize("seconds", [14.9, 30.1])
def test_duration_outside_readme_budget_fails(seconds):
    with pytest.raises(ValueError, match="15–30 s"):
        demo.check_duration(seconds)


def test_duration_inside_budget_passes():
    demo.check_duration(24.0)


def test_media_limits():
    demo.check_media(gif_bytes=4_999_999, fps=15)
    with pytest.raises(ValueError, match="5 MB"):
        demo.check_media(gif_bytes=5_000_000, fps=15)
    with pytest.raises(ValueError, match="15–25 fps"):
        demo.check_media(gif_bytes=1, fps=12)


def test_recording_record_is_reproducible_metadata():
    record = demo.recording_record(
        revision="abc123",
        recorded="2026-09-30",
        width=1280,
        height=720,
        capture_scale=2,
        fps=15,
        duration=24.04,
        waits=[51.3, 14.6],
        models=["gemma4:e4b", "gemma4:12b"],
        files={"gif": "demo.gif"},
    )

    assert record == {
        "source_revision": "abc123",
        "recorded": "2026-09-30",
        "data": "synthetic",
        "width": 1280,
        "height": 720,
        "capture_scale": 2,
        "fps": 15,
        "duration_seconds": 24.0,
        "model_waits_cut_seconds": [51.3, 14.6],
        "models": ["gemma4:e4b", "gemma4:12b"],
        "files": {"gif": "demo.gif"},
        "script": "scripts/record_demo.py",
    }
