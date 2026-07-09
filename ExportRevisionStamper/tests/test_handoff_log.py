import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import handoff_log


def test_append_entry_creates_header_once(tmp_path):
    log_path = str(tmp_path / "handoff_log.csv")

    handoff_log.append_entry(log_path, {
        "timestamp": "2026-07-09T12:00:00",
        "part_name": "bracket",
        "version_number": 7,
        "revision": "G",
        "format": "STEP",
        "filename": "bracket_RevG_20260709.step",
        "vendor_note": "acme corp",
        "doc_had_unsaved_changes": False,
    })
    handoff_log.append_entry(log_path, {
        "timestamp": "2026-07-09T12:05:00",
        "part_name": "bracket",
        "version_number": 8,
        "revision": "H",
        "format": "STL",
        "filename": "bracket_RevH_20260709.stl",
        "vendor_note": "",
        "doc_had_unsaved_changes": True,
    })

    with open(log_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert rows[0]["revision"] == "G"
    assert rows[1]["revision"] == "H"
    assert rows[0].keys() == set(handoff_log.COLUMNS)


def test_append_entry_missing_fields_default_to_empty(tmp_path):
    log_path = str(tmp_path / "handoff_log.csv")
    handoff_log.append_entry(log_path, {"part_name": "bracket"})

    with open(log_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert rows[0]["part_name"] == "bracket"
    assert rows[0]["vendor_note"] == ""
