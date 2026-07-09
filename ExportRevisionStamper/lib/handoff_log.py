"""Local CSV handoff log — a record of what was actually exported and sent.

No Fusion API dependency here on purpose, so this logic can be unit tested
without a running Fusion session.
"""
import csv
import os

COLUMNS = [
    "timestamp",
    "part_name",
    "version_number",
    "revision",
    "format",
    "filename",
    "vendor_note",
    "doc_had_unsaved_changes",
]


def append_entry(log_path: str, entry: dict) -> None:
    """Append one row to the handoff log CSV, writing a header if the file is new."""
    file_exists = os.path.isfile(log_path)
    row = {col: entry.get(col, "") for col in COLUMNS}
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
